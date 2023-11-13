from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError

from rpidrive.controllers.volume import (
    InvalidVolumeNameException,
    InvalidVolumePathException,
    NoPermissionException,
    VolumeNotFoundException,
    VolumePermissionEnum,
    VolumePermissionModel,
    delete_volume,
    get_root_file_id,
    request_volume,
    get_volume_space,
    update_volume,
    update_volume_permission,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    """Request model for update"""

    name: str
    path: str


class _RequestPermModel(BaseModel):
    """Request model for permission update"""

    permissions: List[VolumePermissionModel]


class VolumeDetailView(LoginRequiredMixin, View):
    """Volume detail view"""

    @handle_exceptions(
        known_exc={
            VolumeNotFoundException,
        }
    )
    def get(self, request, volume_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        volume = request_volume(
            request.user, volume_id, VolumePermissionEnum.READ, False
        )
        total, used, free = get_volume_space(volume)
        root_file_id = get_root_file_id(volume)

        return JsonResponse(
            {
                "id": volume.id,
                "name": volume.name,
                "indexing": volume.indexing,
                "path": volume.path,
                "total_space": total,
                "used_space": used,
                "free_space": free,
                "kind": volume.kind,
                "permissions": [
                    {
                        "user": entry.user_id,
                        "permission": entry.permission,
                    }
                    for entry in volume.volumeuser_set.all()
                ],
                "root_file": root_file_id,
            }
        )

    @handle_exceptions(
        known_exc={
            IntegrityError,
            InvalidVolumeNameException,
            InvalidVolumePathException,
            NoPermissionException,
            ValidationError,
            VolumeNotFoundException,
        }
    )
    def post(self, request, volume_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        update_perms = request.GET.get("fields", None) == "permissions"
        if update_perms:
            data = _RequestPermModel.model_validate_json(request.body)
            update_volume_permission(request.user, volume_id, data.permissions)
        else:
            data = _RequestModel.model_validate_json(request.body)
            update_volume(request.user, volume_id, data.name, data.path)
        return JsonResponse({})

    @handle_exceptions(
        known_exc={
            NoPermissionException,
            VolumeNotFoundException,
        }
    )
    def delete(self, request, volume_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle DELETE request"""
        delete_volume(request.user, volume_id)
        return JsonResponse({})
