import uuid

from enum import Enum
from typing import List, Tuple

from django.contrib.auth.models import User
from django.db import models


class VolumeKindEnum(str, Enum):
    """Volume kind enum"""

    HOST_PATH = "hostPath"
    REMOTE_RPI_DRIVE = "remoteRpiDrive"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        """Return enum choices"""
        return [(item.value, item.name) for item in cls]

    @classmethod
    def pairs(cls) -> List[Tuple[str, str]]:
        """Return name-value pairs"""
        return [
            ("Local Storage", cls.HOST_PATH),
            ("Remote RPI Drive", cls.REMOTE_RPI_DRIVE),
        ]


class VolumePermissionEnum(int, Enum):
    """Volume permission enum"""

    NONE = 0
    READ = 10
    READ_WRITE = 20
    ADMIN = 30

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        """Return enum choices"""
        return [(item.value, item.name) for item in cls]

    @classmethod
    def pairs(cls) -> List[Tuple[str, str]]:
        """Return name-value pairs"""
        return [
            ("Read only", cls.READ),
            ("Read-Write", cls.READ_WRITE),
            ("Admin", cls.ADMIN),
        ]


class Volume(models.Model):
    """Volume class"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )
    name = models.TextField(unique=True)
    kind = models.CharField(
        choices=VolumeKindEnum.choices(),
        max_length=30,
    )
    path = models.TextField(unique=True)
    indexing = models.BooleanField(default=False)
    last_indexed = models.DateTimeField(default=None, null=True)

    def __str__(self) -> str:
        return self.name


class VolumeUser(models.Model):
    """Volume user class"""

    volume = models.ForeignKey(
        Volume,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    permission = models.IntegerField(choices=VolumePermissionEnum.choices())

    def __str__(self) -> str:
        return f"{self.volume} - {self.user}"


class FileKindEnum(str, Enum):
    """File kind enum"""

    FILE = "file"
    FOLDER = "folder"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        """Return enum choices"""
        return [(item.value, item.name) for item in cls]


class File(models.Model):
    """File class"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )
    name = models.TextField(
        db_index=True,
    )
    kind = models.CharField(
        choices=FileKindEnum.choices(),
        max_length=20,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        related_name="children",
    )
    volume = models.ForeignKey(
        Volume,
        on_delete=models.CASCADE,
    )
    path_from_vol = models.TextField(
        null=True,
        blank=True,
    )
    media_type = models.TextField(
        null=True,
        blank=True,
    )
    last_modified = models.DateTimeField(
        null=True,
        default=None,
    )
    size = models.PositiveBigIntegerField(default=0)
    metadata = models.JSONField(null=True, default=None)

    def __str__(self):
        return self.path_from_vol


class Playlist(models.Model):
    """Playlist class"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.TextField(db_index=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)


class PlaylistFile(models.Model):
    """PlaylistFile class"""

    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    sequence = models.IntegerField()

    class Meta:
        ordering = ("sequence",)


class PublicFileLink(models.Model):
    """PublicFileLink class"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    expire_time = models.DateTimeField()


class ActivityKindEnum(str, Enum):
    """Activity kind enum"""

    CREATE_VOLUME = "volume.create"
    UPDATE_VOLUME = "volume.update"
    DELETE_VOLUME = "volume.delete"
    UPLOAD_FILE = "file.upload"
    MOVE_FILE = "file.move"
    DELETE_FILE = "file.delete"

    @classmethod
    def choices(cls) -> List[Tuple[str, str]]:
        """Return enum choices"""
        return [(item.value, item.name) for item in cls]


class Activity(models.Model):
    """Activity class"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    timestamp = models.DateTimeField(
        auto_now=True,
        db_index=True,
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    kind = models.TextField(choices=ActivityKindEnum.choices())
    data = models.JSONField()


class JobKind(str, Enum):
    """Job kind enum"""

    INDEX = "index"
    ZIP = "zip"

    @classmethod
    def choices(cls):
        """Return enum choices"""
        return [(item.value, item.name) for item in cls]


class JobStatus(str, Enum):
    """Job status enum"""

    IN_QUEUE = "In queue"
    RUNNING = "Running"
    COMPLETED = "Completed"

    @classmethod
    def choices(cls):
        """Return enum choices"""
        return [(item.value, item.name) for item in cls]


class Job(models.Model):
    """Job class"""

    kind = models.CharField(
        choices=JobKind.choices(),
        max_length=30,
    )
    volume = models.ForeignKey(
        Volume,
        on_delete=models.CASCADE,
        null=True,
    )
    description = models.TextField()
    data = models.JSONField()
    status = models.CharField(choices=JobStatus.choices())
    progress = models.IntegerField(default=0)
    to_stop = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.description
