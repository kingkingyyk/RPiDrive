from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.volume import (
    get_volumes,
    get_volume_space,
)
from rpidrive.views.decorators.generics import handle_exceptions


class VolumeListView(LoginRequiredMixin, View):
    """List volumes view"""

    @handle_exceptions
    def get(self, request, *_args, **_kwargs):
        """Handle GET request"""
        volumes = get_volumes(request.user).order_by("name").all()

        data = [
            {
                "id": volume.id,
                "name": volume.name,
                "indexing": volume.indexing,
                "path": volume.path,
            }
            for volume in volumes
        ]
        for entry in data:
            total, used, free = get_volume_space(entry["path"])
            entry["total_space"] = total
            entry["used_space"] = used
            entry["free_space"] = free

        return JsonResponse({"values": data})
