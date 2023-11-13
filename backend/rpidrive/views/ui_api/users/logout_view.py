from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View


class UserLogoutView(LoginRequiredMixin, View):
    """User login view"""

    def post(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        logout(request)

        response = JsonResponse({})
        response.delete_cookie("csrftoken")
        return response
