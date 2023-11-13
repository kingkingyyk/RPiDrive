from django.core.handlers.wsgi import WSGIRequest
from django.http import StreamingHttpResponse
from django.views import View

from rpidrive.controllers.exceptions import InvalidOperationRequestException
from rpidrive.controllers.file import (
    FileNotFoundException,
    serve_qa_file,
)
from rpidrive.views.decorators.generics import handle_exceptions


class FileQAView(View):
    """File quick access view"""

    @handle_exceptions(
        known_exc={
            FileNotFoundException,
            InvalidOperationRequestException,
        }
    )
    def get(self, request: WSGIRequest, *_args, **_kwargs) -> StreamingHttpResponse:
        """Handle GET request"""
        qa_id = request.GET.get("key", None)
        return serve_qa_file(qa_id, request)
