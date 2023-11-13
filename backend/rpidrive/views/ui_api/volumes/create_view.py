import http

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel

from rpidrive.controllers.volume import (
    NoPermissionException,
    InvalidVolumeNameException,
    InvalidVolumePathException,
    create_volume,
)
from rpidrive.models import VolumeKindEnum
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    """Request model for view"""

    name: str
    kind: VolumeKindEnum
    path: str


class VolumeCreateView(LoginRequiredMixin, View):
    """Create volume view"""

    @handle_exceptions(
        known_exc={
            NoPermissionException,
            IntegrityError,
            InvalidVolumeNameException,
            InvalidVolumePathException,
        }
    )
    def post(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        volume = create_volume(request.user, data.name, data.kind, data.path)
        return JsonResponse({"id": volume.pk}, status=http.HTTPStatus.CREATED)
