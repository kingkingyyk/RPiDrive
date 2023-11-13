import http

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.file import (
    InvalidOperationRequestException,
    FileNotFoundException,
    create_files,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _NoFileException(Exception):
    """No file exception"""


class FileUploadView(LoginRequiredMixin, View):
    """File upload view"""

    _FILE_FORM = "files"
    _PATH_FORM = "paths"

    @handle_exceptions(
        known_exc={
            FileNotFoundException,
            InvalidOperationRequestException,
            _NoFileException,
            NoPermissionException,
        }
    )
    def post(self, request, file_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        if not request.FILES.get(self._FILE_FORM, None):
            raise _NoFileException("No file was uploaded.")

        file_list = request.FILES.getlist(self._FILE_FORM)
        path_list = request.POST.getlist(self._PATH_FORM)
        data = [
            {"file": file_list[idx], "path": path_list[idx]}
            for idx in range(len(file_list))
        ]
        create_files(request.user, file_id, data)

        return JsonResponse({}, status=http.HTTPStatus.CREATED)
