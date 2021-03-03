from django.db import models
from django.db.models import Prefetch
from django.conf import settings
from django.contrib.auth.models import User
import uuid, humanize, os, time, shutil, pytz
from datetime import datetime


class StorageProviderType:
    LOCAL_PATH_NAME = 'Local Storage'
    LOCAL_PATH = 'LOCAL_PATH'

    VALUES = [LOCAL_PATH]
    TYPES = [(LOCAL_PATH_NAME, LOCAL_PATH)]


class FileObjectType:
    FOLDER = 'FOLDER'
    FILE = 'FILE'


class FileExt:
    TYPE_MOVIE = 'movie'
    TYPE_MUSIC = 'music'
    TYPE_PICTURE = 'picture'
    TYPE_CODE = 'code'
    TYPE_COMPRESSED = 'compressed'
    TYPE_EXECUTABLE = 'executable'
    TYPE_LIBRARY = 'library'
    TYPE_BOOK = 'book'

    _TYPE_TO_EXT = {
        TYPE_MOVIE: ['mp4', 'webm'],
        TYPE_MUSIC: ('mp3', 'm4a', 'ogg', 'flac'),
        TYPE_PICTURE: ('jpg', 'bmp', 'gif', 'png'),
        TYPE_CODE: ('cpp', 'java', 'py', 'php', 'cs', 'txt'),
        TYPE_COMPRESSED: ('rar', 'zip', '7z', 'arj', 'bz2', 'cab', 'gz', 'iso',
                                       'lz', 'lzh', 'tar', 'uue', 'xz', 'z', 'zipx'),
        TYPE_EXECUTABLE: ('exe', 'sh', 'bat'),
        TYPE_LIBRARY: ('dll', 'so'),
        TYPE_BOOK: ('epub', 'mobi', 'pdf')

    }
    _EXT_TO_TYPE = {}
    for key, values in _TYPE_TO_EXT.items():
        for val in values:
            _EXT_TO_TYPE[val] = key

    @staticmethod
    def resolve_extension(ext: str) -> str:
        return FileExt._EXT_TO_TYPE.get(ext.lower(), None)


class System(models.Model):
    initialized = models.BooleanField(default=False)
    init_key = models.TextField(default=None, null=True)

    def __str__(self):
        return 'System'


class StorageProviderObjectManager(models.Manager):
    def get_queryset(self):
        return super(StorageProvider, self).get_queryset().prefetch_related(
            Prefetch('storageprovideruser_set', queryset=StorageProviderUser.objects.select_related('user')))


class StorageProvider(models.Model):
    name = models.TextField()
    type = models.CharField(max_length=10)
    path = models.TextField()
    indexing = models.BooleanField(default=False)
    permissions = models.ManyToManyField(User, through='StorageProviderUser')

    def __str__(self):
        return self.name

    @property
    def space(self):
        return shutil.disk_usage(self.path)

    @property
    def used_space(self):
        return self.space[1]

    @property
    def total_space(self):
        return self.space[0]


class LocalFileObjectManager(models.Manager):
    def get_queryset(self):
        return super(LocalFileObjectManager, self).get_queryset().order_by('-obj_type', 'name').select_related('storage_provider', 'parent')


class LocalFileObject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.TextField(db_index=True)
    obj_type = models.CharField(max_length=10)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    storage_provider = models.ForeignKey(StorageProvider, on_delete=models.CASCADE)
    rel_path = models.TextField(null=True, blank=True)
    extension = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    objects = LocalFileObjectManager()
    metadata = models.JSONField(null=True, default=None)

    def _update_extension(self):
        if self.obj_type == FileObjectType.FOLDER:
            self.extension = None
        elif self.obj_type == FileObjectType.FILE:
            self.extension = self.name.lower().split('.')[-1]

    def _update_type(self):
        if self.obj_type == FileObjectType.FOLDER:
            self.type = None
        elif self.obj_type == FileObjectType.FILE:
            self.type = FileExt.resolve_extension(self.extension)

    def update_name(self, new_name: str):
        if self.name != new_name:
            self.name = new_name
            split = self.rel_path.split(os.path.sep)
            split[-1] = self.name
            self.rel_path = os.path.sep.join(split)
            self.save(update_fields=['name', 'rel_path'])

    @property
    def full_path(self):
        return os.path.join(self.storage_provider.path, self.rel_path)

    @property
    def last_modified(self):
        timestamp = os.path.getmtime(self.full_path)
        return datetime.fromtimestamp(timestamp, tz=pytz.timezone(settings.TIME_ZONE))

    @property
    def size(self):
        return os.path.getsize(self.full_path)

    def save(self, *args, **kwargs):
        self._update_extension()
        self._update_type()
        super(LocalFileObject, self).save(*args, **kwargs)

    def __str__(self):
        return self.full_path

class Playlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.TextField(db_index=True)
    files = models.ManyToManyField(LocalFileObject, through='PlaylistFile')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class PlaylistFile(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    file = models.ForeignKey(LocalFileObject, on_delete=models.CASCADE)
    sequence = models.IntegerField()

    class Meta:
        ordering = ('sequence',)

class StorageProviderUser(models.Model):
    storage_provider = models.ForeignKey(
        StorageProvider, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    permission = models.IntegerField()

    class PERMISSION:
        NONE = 0
        READ = 10
        READ_WRITE = 20
        ADMIN = 30

    PERMISSIONS  = (PERMISSION.NONE,
                    PERMISSION.READ,
                    PERMISSION.READ_WRITE, )
    PERMISSION_CHOICES = [
        (PERMISSION.NONE, 'None'),
        (PERMISSION.READ, 'Read'),
        (PERMISSION.READ_WRITE, 'Read & Write'),
    ]
