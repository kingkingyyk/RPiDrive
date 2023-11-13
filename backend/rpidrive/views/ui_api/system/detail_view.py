from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.system import (
    get_cpu_info,
    get_disk_info,
    get_environ_info,
    get_mem_info,
)
from rpidrive.views.decorators.generics import handle_exceptions


class SystemDetailView(LoginRequiredMixin, View):
    """System detail view"""

    @handle_exceptions(
        known_exc={
            NoPermissionException,
        }
    )
    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        return JsonResponse(
            {
                "cpu": get_cpu_info(request.user).model_dump(),
                "memory": get_mem_info(request.user).model_dump(),
                "disks": [x.model_dump() for x in get_disk_info(request.user)],
                "environment": get_environ_info(request.user).model_dump(),
            }
        )
