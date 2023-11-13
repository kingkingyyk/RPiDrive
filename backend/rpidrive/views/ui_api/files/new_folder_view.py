import http

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.file import (
    InvalidFileNameException,
    InvalidOperationRequestException,
    FileNotFoundException,
    create_folder,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    """Model for view"""

    name: str


class NewFolderView(LoginRequiredMixin, View):
    """New folder view"""

    @handle_exceptions(
        known_exc={
            InvalidFileNameException,
            InvalidOperationRequestException,
            FileNotFoundException,
            NoPermissionException,
            ValidationError,
        }
    )
    def post(self, request, file_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        folder = create_folder(request.user, file_id, data.name)
        return JsonResponse({"id": folder.pk}, status=http.HTTPStatus.CREATED)
