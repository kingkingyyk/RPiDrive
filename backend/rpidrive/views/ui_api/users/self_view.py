from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View


class UserSelfView(LoginRequiredMixin, View):
    """User self view"""

    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle GET response"""
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        user = request.user
        return JsonResponse(
            {
                "id": user.pk,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_superuser": user.is_superuser,
                "is_active": user.is_active,
                "email": user.email,
            }
        )
