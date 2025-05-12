from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.file import get_file_full_path, search_files
from rpidrive.views.decorators.generics import handle_exceptions


class _InvalidKeywordException(Exception):
    """Invalid keyword exception"""


class FileSearchView(LoginRequiredMixin, View):
    """File search view"""

    @handle_exceptions(
        known_exc={
            _InvalidKeywordException,
            NotImplementedError,
        }
    )
    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        keyword = request.GET.get("keyword", None)
        if not keyword:
            raise _InvalidKeywordException("Missing keyword.")
        files = search_files(request.user, keyword).select_related("volume")
        data = [
            {
                "id": file.pk,
                "name": file.name,
                "path": get_file_full_path(file),
                "last_modified": file.last_modified,
                "size": file.size,
                "media_type": file.media_type,
                "kind": file.kind,
            }
            for file in files
        ]
        return JsonResponse({"values": data})
