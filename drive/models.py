from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import get_current_timezone
from enum import Enum
from datetime import datetime, timedelta
import uuid, shutil, os, humanize


class Drive(models.Model):
    name = models.CharField(max_length=20)


class Storage(models.Model):
    base_path = models.TextField()
    drive = models.ForeignKey(Drive, on_delete=models.CASCADE)
    primary = models.BooleanField()

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


class FileObject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relative_path = models.TextField(unique=True)
    permissions = models.ManyToManyField('Permission')
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    last_modified = models.DateTimeField()
    size = models.BigIntegerField()

    @property
    def name(self):
        return self.relative_path.split(os.path.sep)[-1]

    @property
    def size_natural(self):
        pass

    @property
    def last_modified_natural(self):
        delta = datetime.now(tz=get_current_timezone()) - self.last_modified
        return humanize.naturaldelta(delta)+' ago' if delta < timedelta(days=2) else humanize.naturalday(self.last_modified)

    @property
    def class_name(self):
        return self.__class__.__name__


class Folder(FileObject):

    @property
    def size_natural(self):
        return '-'


class File(FileObject):

    @property
    def size_natural(self):
        return Storage.natural_space(self.size)

    @property
    def file_extension(self):
        name = self.relative_path.split(os.path.sep)[-1]
        return name.split('.')[-1].lower()

    @property
    def is_movie(self):
        return self.file_extension == 'mp4'

    @property
    def is_music(self):
        return self.file_extension in ('mp3', 'm4a')

    @property
    def is_picture(self):
        return self.file_extension in ('jpg', 'bmp', 'gif', 'png')

    @property
    def is_code(self):
        return self.file_extension in ('cpp', 'java', 'py', 'php', 'cs', 'txt')

    @property
    def preview_type(self):
        if self.is_movie:
            return 'movie'
        elif self.is_music:
            return 'music'
        elif self.is_picture:
            return 'picture'
        elif self.is_code:
            return 'text'
        return 'none'


class PermissionType(Enum):
    read = 'READ'
    update = 'UPDATE'
    delete = 'DELETE'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class Permission(models.Model):
    file_object = models.ForeignKey(FileObject, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=PermissionType.choices())


class DownloadStatus(Enum):
    queue = 'In queue'
    downloading = 'Downloading'
    finished = 'Finished'
    paused = 'Paused'
    error = 'Error'
    stopped = 'Stopped'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class Download(models.Model):
    file = models.ForeignKey(FileObject, on_delete=models.CASCADE)
    source_url = models.URLField()
    auth = models.BooleanField()
    username = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    progress = models.FloatField()
    status = models.TextField()
    detailed_status = models.TextField(blank=True, null=True)
    to_stop = models.BooleanField()
    to_delete_file = models.BooleanField()