from django.db import models
from django.utils.timezone import get_current_timezone
from polymorphic.models import PolymorphicModel
from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone
import shutil, os, humanize, uuid, humanize

class Settings(models.Model):
    name = models.CharField(max_length=50)

class Storage(models.Model):
    base_path = models.TextField()
    primary = models.BooleanField()

    @property
    def available(self):
        return os.path.exists(self.base_path)

    def __str__(self):
        return self.base_path

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
        
class File(PolymorphicModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    relative_path = models.TextField(unique=True, db_index=True)
    parent_folder = models.ForeignKey('FolderObject', on_delete=models.CASCADE, null=True)
    last_modified = models.DateTimeField()
    content_type = models.TextField(default='application/octet-stream')

    def __str__(self):
        return self.relative_path

    @property
    def class_name(self):
        return self.__class__.__name__

    @property
    def natural_last_modified(self):
        last_m = self.last_modified
        delta = datetime.now(tz=get_current_timezone()) - last_m
        return humanize.naturaldelta(delta)+' ago' if delta < timedelta(days=2) else humanize.naturalday(last_m)

    @property
    def natural_size(self):
        return '-'

class FolderObject(File):
    pass

class FileObject(File):
    size = models.PositiveIntegerField()

    @property
    def natural_size(self):
        return Storage.natural_space(self.size)

class PictureFileObject(FileObject):
    body_make = models.TextField(blank=True, null=True, db_index=True)
    body_model = models.TextField(blank=True, null=True, db_index=True)
    lens_make = models.TextField(blank=True, null=True, db_index=True)
    lens_model = models.TextField(blank=True, null=True, db_index=True)
    iso = models.TextField(blank=True, null=True)
    aperture = models.TextField(blank=True, null=True)
    shutter_speed = models.TextField(blank=True, null=True)
    focal_length = models.TextField(blank=True, null=True)

class MusicFileObject(FileObject):
    title = models.TextField()
    artist = models.TextField(default="Unknown Artist", db_index=True)
    album = models.TextField(default="Unknown Album", db_index=True)
    genre = models.TextField(default="", blank=True, db_index=True)

class FileTypes:
    PICTURE = "PICTURE"
    MUSIC = "MUSIC"
    VIDEO = "VIDEO"
    COMPRESSED = "COMPRESSED"
    CODE = "CODE"
    EXECUTABLE = "EXECUTABLE"
    LIBRARY = "LIBRARY"
    BOOK = "BOOK"
    OTHER = "OTHER"

    @staticmethod
    def get_type(file_path):
        file_path = os.path.basename(file_path).lower()
        file_ext = file_path.split('.')[-1]
        if file_ext in ("mp4", "webm"):
            return FileTypes.VIDEO
        elif file_ext in ("mp3", "m4a", "ogg", 'flac'):
            return FileTypes.MUSIC
        elif file_ext in ("jpg", "bmp", "gif", "png"):
            return FileTypes.PICTURE
        elif file_ext in ('rar', 'zip', '7z', 'arj', 'bz2', 'cab', 'gz', 'iso',
                                       'lz', 'lzh', 'tar', 'uue', 'xz', 'z', 'zipx'):
            return FileTypes.COMPRESSED
        elif file_ext in ('cpp', 'java', 'py', 'php', 'cs', 'txt'):
            return FileTypes.CODE
        elif file_ext in ('exe', 'sh', 'bat'):
            return FileTypes.EXECUTABLE
        elif file_ext in ('dll', 'so'):
            return FileTypes.LIBRARY
        elif file_ext in ('epub', 'mobi', 'pdf'):
            return FileTypes.BOOK
        return FileTypes.OTHER