from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.file import (
    InvalidOperationRequestException,
    FileNotFoundException,
    share_file,
)
from rpidrive.views.decorators.generics import handle_exceptions


class FileShareView(LoginRequiredMixin, View):
    """File share view"""

    @handle_exceptions(
        known_exc={
            InvalidOperationRequestException,
            FileNotFoundException,
            NoPermissionException,
        }
    )
    def post(self, request, file_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        link = share_file(request.user, file_id)
        return JsonResponse({"id": link.pk})
