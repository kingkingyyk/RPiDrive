from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.handlers.wsgi import WSGIRequest
from django.http import StreamingHttpResponse
from django.views import View

from rpidrive.controllers.exceptions import (
    InvalidOperationRequestException,
    NoPermissionException,
)
from rpidrive.controllers.file import (
    FileNotFoundException,
    serve_file,
)
from rpidrive.views.decorators.generics import handle_exceptions


class FileDownloadView(LoginRequiredMixin, View):
    """File download view"""

    @handle_exceptions(
        known_exc={
            InvalidOperationRequestException,
            FileNotFoundException,
            NoPermissionException,
        }
    )
    def get(
        self, request: WSGIRequest, file_id: str, *_args, **_kwargs
    ) -> StreamingHttpResponse:
        """Handle GET request"""
        return serve_file(request.user, file_id, request)
