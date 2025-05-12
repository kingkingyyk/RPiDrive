from enum import Enum
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError

from rpidrive.controllers.file import (
    InvalidOperationRequestException,
    FileNotFoundException,
    move_files,
)
from rpidrive.controllers.volume import VolumeNotFoundException
from rpidrive.views.decorators.generics import handle_exceptions


class _MoveStrategy(str, Enum):
    """Enum for strategies"""

    RENAME = "rename"
    OVERWRITE = "overwrite"


class _RequestModel(BaseModel):
    """Model for view"""

    files: List[str]
    strategy: _MoveStrategy
    move_to: str


class FileMoveView(LoginRequiredMixin, View):
    """File move view"""

    @handle_exceptions(
        known_exc={
            InvalidOperationRequestException,
            FileNotFoundException,
            ValidationError,
            VolumeNotFoundException,
        }
    )
    def post(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        move_files(
            request.user,
            data.files,
            data.move_to,
            data.strategy == _MoveStrategy.RENAME,
        )
        return JsonResponse({})
