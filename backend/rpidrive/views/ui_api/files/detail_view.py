from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.file import (
    FileNotFoundException,
    delete_files,
    get_file,
    get_file_parents,
)
from rpidrive.models import File
from rpidrive.views.decorators.generics import handle_exceptions


class FileDetailView(LoginRequiredMixin, View):
    """File detail view"""

    _VOLUME_FIELD = "volume"
    _PARENT_FIELD = "parent"
    _CHILDREN_FIELD = "children"
    _PATH_FIELD = "path"

    _SELECT_FIELDS = (
        _VOLUME_FIELD,
        _PARENT_FIELD,
    )
    _PREFETCH_FIELDS = (_CHILDREN_FIELD,)

    @staticmethod
    def _get_file_as_raw(file: File) -> Dict[str, Any]:
        if not file:
            return None
        return {
            "id": file.pk,
            "name": file.name,
            "kind": file.kind,
            "last_modified": file.last_modified,
            "size": file.size,
            "metadata": file.metadata,
            "parent_id": file.parent_id,
            "media_type": file.media_type,
        }

    @staticmethod
    def _get_file_as_raw_simple(file: File) -> Dict[str, Any]:
        if not file:
            return None
        return {
            "id": file.pk,
            "name": file.name,
        }

    @handle_exceptions(
        known_exc={
            FileNotFoundException,
        }
    )
    def get(self, request, file_id: str, *args, **kwargs) -> JsonResponse:
        """Handle GET request"""
        fields = set(request.GET.get("fields", "").split(","))
        select_related = {x for x in self._SELECT_FIELDS if x in fields}
        prefetch_related = {x for x in self._PREFETCH_FIELDS if x in fields}

        file = get_file(request.user, file_id, select_related, prefetch_related)
        raw_data = FileDetailView._get_file_as_raw(file)

        # Add extra fields
        if self._VOLUME_FIELD in select_related:
            raw_data[self._VOLUME_FIELD] = {
                "id": file.volume.pk,
                "name": file.volume.name,
            }
        if self._PARENT_FIELD in select_related:
            raw_data[self._PARENT_FIELD] = FileDetailView._get_file_as_raw_simple(
                file.parent
            )
        if self._CHILDREN_FIELD in prefetch_related:
            raw_data[self._CHILDREN_FIELD] = [
                FileDetailView._get_file_as_raw(child)
                for child in file.children.order_by("-kind", "name").all()
            ]
        if self._PATH_FIELD in fields:
            raw_data[self._PATH_FIELD] = [
                FileDetailView._get_file_as_raw_simple(comp)
                for comp in get_file_parents(file)
            ]

        return JsonResponse(raw_data)

    def delete(self, request, file_id: str, *args, **kwargs) -> JsonResponse:
        """Handle DELETE request"""
        delete_files(request.user, [file_id])
        return JsonResponse({})
