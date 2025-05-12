from typing import Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.exceptions import (
    NoPermissionException,
)
from rpidrive.controllers.user import get_users
from rpidrive.models import VolumeUser, VolumePermissionEnum

from rpidrive.views.decorators.generics import handle_exceptions


class UserListView(LoginRequiredMixin, View):
    """List users view"""

    @staticmethod
    def _serialize_user(user: User, with_extras: bool) -> Dict:
        data = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
        if with_extras:
            data = {
                **data,
                **{
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser,
                    "last_login": user.last_login,
                },
            }
        return data

    @handle_exceptions(
        known_exc={
            NoPermissionException,
        }
    )
    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        if not request.user.is_superuser:
            can_write_volume = VolumeUser.objects.filter(
                user=request.user, permission__gte=VolumePermissionEnum.READ_WRITE
            ).exists()
            if not can_write_volume:
                raise NoPermissionException("No permission.")

        users = get_users(request.user).order_by("username").all()
        list_data = [
            UserListView._serialize_user(user, request.user.is_superuser)
            for user in users
        ]

        return JsonResponse({"values": list_data})
