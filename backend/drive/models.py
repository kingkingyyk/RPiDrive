import os
import shutil
import uuid

from enum import Enum

from django.db import models
from django.db.models import Prefetch
from django.contrib.auth.models import User


class StorageProviderType:
    """StorageProviderType definitions"""
    LOCAL_PATH_NAME = 'Local Storage'
    LOCAL_PATH = 'LOCAL_PATH'

    VALUES = [LOCAL_PATH]
    TYPES = [(LOCAL_PATH_NAME, LOCAL_PATH)]


class FileObjectType:
    """FileObjectType definitions"""
    FOLDER = 'FOLDER'
    FILE = 'FILE'


class FileExt:
    """FileExt definitions"""
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
        """Convert ext to type"""
        return FileExt._EXT_TO_TYPE.get(ext.lower(), None)


class System(models.Model):
    """System definition"""
    initialized = models.BooleanField(default=False)
    init_key = models.TextField(default=None, null=True)

    def __str__(self):
        return 'System'


class StorageProviderObjectManager(models.Manager):
    """Default StorageProvider query set"""
    def get_queryset(self):
        """Provides queryset"""
        return super().get_queryset().prefetch_related(
            Prefetch('storageprovideruser_set',
            queryset=StorageProviderUser.objects.select_related('user')))


class StorageProvider(models.Model):
    """StorageProvider definition"""
    name = models.TextField()
    type = models.CharField(max_length=10)
    path = models.TextField()
    indexing = models.BooleanField(default=False)
    permissions = models.ManyToManyField(User, through='StorageProviderUser')
    last_indexed = models.DateTimeField(default=None, null=True)

    objects = StorageProviderObjectManager()

    def __str__(self):
        return self.name

    @property
    def space(self):
        """Returns disk usage values"""
        return shutil.disk_usage(self.path)

    @property
    def used_space(self):
        """Returns used space"""
        return self.space[1]

    @property
    def total_space(self):
        """Returns total space"""
        return self.space[0]


class LocalFileObjectManager(models.Manager):
    """LocalFileObject default query set"""
    def get_queryset(self):
        """Returns query set"""
        return super().get_queryset().order_by(
            '-obj_type', 'name').select_related('storage_provider', 'parent')


class LocalFileObject(models.Model):
    """LocalFileObject definition"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.TextField(db_index=True)
    obj_type = models.CharField(max_length=10)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True, blank=True,
                               related_name='children')
    storage_provider = models.ForeignKey(StorageProvider,
                                         on_delete=models.CASCADE)
    rel_path = models.TextField(null=True, blank=True)
    extension = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    last_modified = models.DateTimeField(null=True, default=None)
    size = models.PositiveBigIntegerField(default=0)
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
        """Update name and rel_path"""
        if self.name != new_name:
            self.name = new_name
            split = self.rel_path.split(os.path.sep)
            split[-1] = self.name
            self.rel_path = os.path.sep.join(split)
            self.save(update_fields=['name', 'rel_path'])

    @property
    def full_path(self):
        """Returns full path of this file"""
        return os.path.join(self.storage_provider.path, self.rel_path)

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):
        """Save method"""
        self._update_extension()
        self._update_type()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_path

class Playlist(models.Model):
    """Playlist definition"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.TextField(db_index=True)
    files = models.ManyToManyField(LocalFileObject, through='PlaylistFile')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class PlaylistFile(models.Model):
    """PlaylistFile definition"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    file = models.ForeignKey(LocalFileObject, on_delete=models.CASCADE)
    sequence = models.IntegerField()

    class Meta:
        ordering = ('sequence',)

class StorageProviderUser(models.Model):
    """StorageProvider permission definition"""
    storage_provider = models.ForeignKey(
        StorageProvider, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    permission = models.IntegerField()

    class PERMISSION:
        """Permission levels"""
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

class Job(models.Model):
    """Job object"""

    class TaskTypes(str, Enum):
        """Task type enum"""
        INDEX = 'index'
        ZIP = 'zip'

        @classmethod
        def choices(cls):
            """Return enum choices"""
            return [(item.value, item.name) for item in cls]

    task_type = models.CharField(
        max_length=20,
        choices=TaskTypes.choices(),
    )
    description = models.TextField()
    data = models.TextField(null=True)
    progress_info = models.TextField(
        null=True,
        default='In queue',
    )
    progress_value = models.IntegerField(default=0)
