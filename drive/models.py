from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import get_current_timezone
from .enum import *
from datetime import datetime, timedelta
import uuid, shutil, os, humanize, time


class Drive(models.Model):
    name = models.CharField(max_length=20)
    downloader_start = models.DateTimeField()

    def __str__(self):
        return self.name


class Storage(models.Model):
    base_path = models.TextField()
    drive = models.ForeignKey(Drive, on_delete=models.CASCADE)
    primary = models.BooleanField()
    is_synching = models.BooleanField()
    last_sync_status = models.TextField(blank=True, null=True)
    last_sync_time = models.DateTimeField(null=True)

    @staticmethod
    def natural_space(value):
        unit = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        idx = 0
        while value > 2**10:
            value /= 2**10
            idx += 1
        value_str = '{:.1f}'.format(value)
        if value_str.endswith('.0'):
            value_str = value_str[:-2]
        return '{:s} {:s}'.format(value_str, unit[idx])

    @property
    def total_space(self):
        return shutil.disk_usage(self.base_path)[0]

    @property
    def total_space_natural(self):
        return Storage.natural_space(self.total_space)

    @property
    def used_space(self):
        return shutil.disk_usage(self.base_path)[1]

    @property
    def used_space_natural(self):
        return Storage.natural_space(self.used_space)

    @property
    def free_space(self):
        return shutil.disk_usage(self.base_path)[2]

    @property
    def free_space_natural(self):
        return Storage.natural_space(self.free_space)

    @property
    def ui_text_natural(self):
        return self.used_space_natural + ' used of ' + self.total_space_natural

    @property
    def usage_percentage(self):
        return int(self.used_space * 100 / self.total_space)

    @property
    def available(self):
        return os.path.exists(self.base_path)

    @property
    def last_sync_time_natural(self):
        if self.last_sync_time is None:
            return '-'
        else:
            delta = datetime.now(tz=get_current_timezone()) - self.last_sync_time
            return humanize.naturaldelta(delta)+' ago' if delta < timedelta(days=2) else humanize.naturalday(self.last_sync_time)

    def __str__(self):
        return self.base_path


class FileObject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relative_path = models.TextField(unique=True)
    permissions = models.ManyToManyField('Permission')
    parent_folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True)
    name = models.TextField()

    class Meta:
        abstract = True

    @property
    def size_natural(self):
        pass

    @property
    def last_modified_natural(self):
        last_m = self.last_modified
        delta = datetime.now() - last_m
        return humanize.naturaldelta(delta)+' ago' if delta < timedelta(days=2) else humanize.naturalday(last_m)

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def last_modified(self):
        return datetime.fromtimestamp(os.path.getmtime(self.real_path))

    @property
    def size(self):
        return os.path.getsize(self.real_path)

    @property
    def real_path(self):
        from .utils.model_utils import ModelUtils
        return os.path.join(ModelUtils.get_storage().base_path, self.relative_path)

    def __str__(self):
        return self.relative_path


class Folder(FileObject):

    @property
    def size_natural(self):
        return '-'


class FileType:
    lookup_type_to_ext = {
        'movie': ['mp4', 'webm'],
        'music': ('mp3', 'm4a', 'ogg'),
        'picture': ('jpg', 'bmp', 'gif', 'png'),
        'code': ('cpp', 'java', 'py', 'php', 'cs', 'txt'),
        'compressed': ('rar', 'zip', '7z', 'arj', 'bz2', 'cab', 'gz', 'iso',
                                       'lz', 'lzh', 'tar', 'uue', 'xz', 'z', 'zipx'),
        'executable': ('exe', 'sh', 'bat'),
        'library': ('dll', 'so'),
        'book': ('epub', 'mobi', 'pdf')

    }
    lookup_ext_to_type = {}
    for key, values in lookup_type_to_ext.items():
        for val in values:
            lookup_ext_to_type[val] = key


class File(FileObject):
    file_extension = models.TextField()

    @staticmethod
    def extract_file_extension(f):
        return f.split(os.path.sep)[-1].split('.')[-1].lower()

    @property
    def size_natural(self):
        return Storage.natural_space(self.size)

    @property
    def is_movie(self):
        return self.file_extension in FileType.lookup_type_to_ext['movie']

    @property
    def is_music(self):
        return self.file_extension in FileType.lookup_type_to_ext['music']

    @property
    def is_picture(self):
        return self.file_extension in FileType.lookup_type_to_ext['picture']

    @property
    def is_code(self):
        return self.file_extension in FileType.lookup_type_to_ext['code']

    @property
    def is_compressed(self):
        return self.file_extension in FileType.lookup_type_to_ext['compressed']

    @property
    def is_executable(self):
        return self.file_extension in FileType.lookup_type_to_ext['executable']

    @property
    def is_library(self):
        return self.file_extension in FileType.lookup_type_to_ext['library']

    @property
    def is_book(self):
        return self.file_extension in FileType.lookup_type_to_ext['book']

    @property
    def preview_type(self):
        return FileType.lookup_ext_to_type.get(self.file_extension, 'none')


class Permission(models.Model):
    folder_obj = models.OneToOneField(Folder, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=PermissionType.choices())


class Download(models.Model):
    file = models.OneToOneField(File, on_delete=models.CASCADE)
    source_url = models.URLField()
    auth = models.BooleanField()
    username = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    progress = models.FloatField()
    status = models.TextField()
    detailed_status = models.TextField(blank=True, null=True)
    to_stop = models.BooleanField()
    to_delete_file = models.BooleanField()
    add_time = models.DateTimeField()
    downloader_status = models.TextField(blank=True, null=True)

    @property
    def operation_done(self):
        return self.status not in [DownloadStatus.queue.value, DownloadStatus.downloading.value]

    def __str__(self):
        return self.source_url + ' -> ' + str(self.file)


class Synchronizer(models.Model):
    file = models.OneToOneField(File, on_delete=models.CASCADE)
    day_mask = models.IntegerField(default=0b1111111)
    period = models.IntegerField(default=15)
