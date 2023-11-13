from typing import List, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError

from rpidrive.controllers.exceptions import (
    InvalidOperationRequestException,
    NoPermissionException,
)
from rpidrive.controllers.file import (
    InvalidFileNameException,
    compress_files,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    """Model for view"""

    files: List[str]
    compress_dir: Optional[str]
    compress_name: Optional[str]


class FileCompressView(LoginRequiredMixin, View):
    """File compress view"""

    @handle_exceptions(
        known_exc={
            InvalidFileNameException,
            InvalidOperationRequestException,
            NoPermissionException,
            ValidationError,
        }
    )
    def post(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        compress_files(request.user, data.files, data.compress_dir, data.compress_name)
        return JsonResponse({})
