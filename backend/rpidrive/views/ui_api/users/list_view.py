from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View

from rpidrive.controllers.user import get_users


class UserListView(LoginRequiredMixin, View):
    """List users view"""

    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET request"""
        users = get_users(request.user).all()
        list_data = [
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "last_login": user.last_login,
            }
            for user in users
        ]

        return JsonResponse({"values": list_data})
