from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.volume import (
    NoPermissionException,
    VolumeNotFoundException,
    perform_index,
)
from rpidrive.views.decorators.generics import handle_exceptions


class VolumeIndexView(LoginRequiredMixin, View):
    """Volume index view"""

    @handle_exceptions(
        known_exc={
            NoPermissionException,
            VolumeNotFoundException,
        }
    )
    def post(self, request, volume_id: str, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        perform_index(request.user, volume_id)
        return JsonResponse({})
