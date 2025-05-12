from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.file import (
    InvalidFileNameException,
    FileNotFoundException,
    rename_file,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    """Model for view"""

    name: str


class FileRenameView(LoginRequiredMixin, View):
    """File rename view"""

    @handle_exceptions(
        known_exc={
            InvalidFileNameException,
            FileNotFoundException,
            NoPermissionException,
            ValidationError,
        }
    )
    def post(self, request, file_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        rename_file(request.user, file_id, data.name)
        return JsonResponse({})
