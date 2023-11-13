from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.system import get_network_info
from rpidrive.views.decorators.generics import handle_exceptions


class SystemNetworkView(LoginRequiredMixin, View):
    """System network view"""

    @handle_exceptions(
        known_exc={
            NoPermissionException,
        }
    )
    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        return JsonResponse(get_network_info(request.user).model_dump())
