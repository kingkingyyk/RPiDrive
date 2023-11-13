from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.file import (
    InvalidFileNameException,
    FileNotFoundException,
    delete_files,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    """Model for view"""

    files: List[str]


class FileDeleteView(LoginRequiredMixin, View):
    """File delete view"""

    @handle_exceptions(
        known_exc={
            InvalidFileNameException,
            FileNotFoundException,
            NoPermissionException,
            ValidationError,
        }
    )
    def post(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        delete_files(request.user, data.files)
        return JsonResponse({})
