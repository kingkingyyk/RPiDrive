from uuid import UUID

from django.contrib.auth.models import User
from pydantic import BaseModel

from rpidrive.models import (
    Activity,
    ActivityKindEnum,
    Volume,
)


class CreateVolumeActivityModel(BaseModel):
    """Create volume activity model"""

    volume_id: UUID


class UpdateVolumeActivityModel(BaseModel):
    """Create volume activity model"""

    volume_id: UUID


class DeleteVolumeActivityModel(BaseModel):
    """Create volume activity model"""

    volume_name: str


def add_create_volume_activity(
    user: User,
    volume: Volume,
):
    """Add create volume activity entry"""
    Activity.objects.create(
        actor=user,
        kind=ActivityKindEnum.CREATE_VOLUME,
        data=(CreateVolumeActivityModel(volume_id=volume.pk).model_dump(mode="json")),
    )


def add_update_volume_activity(
    user: User,
    volume: Volume,
):
    """Add update volume activity entry"""
    Activity.objects.create(
        actor=user,
        kind=ActivityKindEnum.UPDATE_VOLUME,
        data=(UpdateVolumeActivityModel(volume_id=volume.pk).model_dump(mode="json")),
    )


def add_delete_volume_activity(
    user: User,
    volume: Volume,
):
    """Add delete volume activity entry"""
    Activity.objects.create(
        actor=user,
        kind=ActivityKindEnum.DELETE_VOLUME,
        data=(
            DeleteVolumeActivityModel(volume_name=volume.name).model_dump(mode="json")
        ),
    )
