from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.models import VolumePermissionEnum


class VolumePermissionView(LoginRequiredMixin, View):
    """Volume kind view"""

    def get(self, _request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        return JsonResponse(
            {
                "values": [
                    {
                        "name": x[0],
                        "value": x[1],
                    }
                    for x in VolumePermissionEnum.pairs()
                ]
            }
        )
