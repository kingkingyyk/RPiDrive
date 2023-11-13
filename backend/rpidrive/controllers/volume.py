import logging
import os
import shutil

from pathlib import Path
from typing import List, Tuple, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, QuerySet
from pydantic import BaseModel

from rpidrive.controllers.activity import (
    add_create_volume_activity,
    add_delete_volume_activity,
    add_update_volume_activity,
)
from rpidrive.controllers.exceptions import (
    NoPermissionException,
)
from rpidrive.models import (
    File,
    FileKindEnum,
    Volume,
    VolumeKindEnum,
    VolumePermissionEnum,
    VolumeUser,
)


class VolumeNotFoundException(Exception):
    """Volume not found exception"""


class InvalidVolumePathException(Exception):
    """Invalid volume path exception"""


class InvalidVolumeNameException(Exception):
    """Invalid volume name exception"""


class VolumePermissionModel(BaseModel):
    """Volume permission model"""

    user: int
    permission: VolumePermissionEnum


logger = logging.getLogger(__name__)


def _get_volume_permission(
    volume: Volume,
    user: User,
) -> int:
    if user.is_superuser:
        return VolumePermissionEnum.ADMIN.value
    role = volume.volumeuser_set.filter(user=user).first()
    if not role:
        return VolumePermissionEnum.NONE.value
    return role.permission


def request_volume(user: User, volume_id: str, min_level: int, write: bool) -> Volume:
    """Request volume with permissions"""
    volume = Volume.objects.filter(pk=volume_id).prefetch_related("volumeuser_set")
    if write:
        volume = volume.select_for_update(of=("self",))
    volume = volume.first()

    if not volume:
        raise VolumeNotFoundException("Volume not found.")
    level = _get_volume_permission(volume, user)
    if level == VolumePermissionEnum.NONE:
        raise VolumeNotFoundException("Volume not found.")
    if level < min_level:
        raise NoPermissionException("No permission")
    return volume


def create_volume(
    user: User,
    name: str,
    kind: VolumeKindEnum,
    path: str,
) -> Volume:
    """Create volume"""
    if not user.is_superuser:
        raise NoPermissionException("No permission.")
    name = name.strip()
    if not name:
        raise InvalidVolumeNameException("Invalid volume name.")
    path = os.path.abspath(path.strip())
    validate_volume_path(path, [])

    with transaction.atomic():
        volume = Volume.objects.create(name=name, kind=kind, path=path, indexing=True)
        add_create_volume_activity(user, volume)
        # Create root folder entry
        File.objects.create(
            name="",
            kind=FileKindEnum.FOLDER,
            volume=volume,
            path_from_vol=os.path.sep,
        )
    return volume


def get_volumes(user: User) -> QuerySet:
    """Get viewable volumes by user"""
    if user.is_superuser:
        return Volume.objects
    volume_pks = list(
        VolumeUser.objects.filter(
            Q(user=user) & Q(permission__gte=VolumePermissionEnum.READ)
        )
        .values_list("volume_id", flat=True)
        .distinct()
    )
    return Volume.objects.filter(pk__in=volume_pks)


def update_volume(user: User, p_k: str, name: str, path: str):
    """Update volume"""
    with transaction.atomic():
        volume = request_volume(user, p_k, VolumePermissionEnum.READ_WRITE, True)

        name = name.strip()
        if not name:
            raise InvalidVolumeNameException()
        path = os.path.abspath(path.strip())
        validate_volume_path(path, [p_k])

        volume.name = name
        if volume.path != path:
            volume.path = path
            volume.indexing = True
        volume.save()
        add_update_volume_activity(user, volume)

        return volume


def update_volume_permission(
    user: User, p_k: str, permissions: List[VolumePermissionModel]
):
    """Update volume permission"""
    with transaction.atomic():
        volume = request_volume(user, p_k, VolumePermissionEnum.ADMIN, True)
        role = _get_volume_permission(volume, user)

        volume.volumeuser_set.all().delete()
        new_entries = [
            VolumeUser(
                volume=volume,
                user_id=entry.user,
                permission=entry.permission
                if entry.user != user.pk
                else role,  # Can't downgrade self.
            )
            for entry in permissions
        ]
        VolumeUser.objects.bulk_create(new_entries, batch_size=settings.BULK_BATCH_SIZE)


def delete_volume(user: User, p_k: str):
    """Delete volume"""
    with transaction.atomic():
        volume = request_volume(user, p_k, VolumePermissionEnum.ADMIN, True)
        volume.delete()
        add_delete_volume_activity(user, volume)


def validate_volume_path(check_path: str, filt: List[str]):
    """Except volume path"""
    check_path = os.path.abspath(check_path)
    while check_path.endswith(os.path.sep):
        check_path = check_path[:-1]

    if not os.path.exists(check_path):
        raise InvalidVolumePathException("Path doesn't exist.")
    if not os.path.isdir(check_path):
        raise InvalidVolumePathException("Path is not a directory.")

    # Check subfolder
    existing_paths: List[str] = list(
        Volume.objects.exclude(pk__in=filt).values_list("path", flat=True)
    )
    for path in existing_paths:
        if path.startswith(check_path):
            raise InvalidVolumePathException(
                "The subfolder of this path is already added."
            )

    # Make sure the parent of the path is not added yet
    p_obj = Path(check_path)
    parents = {str(p_obj)}
    while p_obj != p_obj.parent:
        p_obj = p_obj.parent
        parents.add(str(p_obj))
    for path in existing_paths:
        if path in parents:
            raise InvalidVolumePathException(
                "The parent folder of this path is already added."
            )


def get_volume_space(volume: Union[str, Volume]) -> Tuple[int, int, int]:
    """Get space of volume"""
    try:
        if isinstance(volume, Volume):
            volume = volume.path
        return shutil.disk_usage(volume)
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Error retrieving volume space.")
        return (0, 0, 0)


def get_root_file_id(volume: Volume) -> str:
    """Get root file ID of volume"""
    return (
        File.objects.filter(Q(volume=volume) & Q(parent=None))
        .values_list("pk", flat=True)
        .first()
    )


def perform_index(user: User, volume_id: str):
    """Mark volume to perform index"""
    with transaction.atomic():
        volume = request_volume(user, volume_id, VolumePermissionEnum.ADMIN, True)
        volume.indexing = True
        volume.save(update_fields=["indexing"])
