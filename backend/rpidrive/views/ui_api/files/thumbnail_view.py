from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import StreamingHttpResponse
from django.views import View

from rpidrive.controllers.exceptions import (
    InvalidOperationRequestException,
    NoPermissionException,
)
from rpidrive.controllers.file import (
    FileNotFoundException,
    serve_file_thumbnail,
)
from rpidrive.views.decorators.generics import handle_exceptions


class FileThumbnailView(LoginRequiredMixin, View):
    """File thumbnail view"""

    @handle_exceptions(
        known_exc={
            InvalidOperationRequestException,
            FileNotFoundException,
            NoPermissionException,
        }
    )
    def get(self, request, file_id: str, *_args, **_kwargs) -> StreamingHttpResponse:
        """Handle GET request"""
        return serve_file_thumbnail(request.user, file_id)
