import http

from django.http.response import JsonResponse
from django.views import View


class UserLoggedInView(View):
    """User logged in view"""

    def get(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        flag = request.user.is_authenticated
        return JsonResponse(
            {"flag": flag},
            status=http.HTTPStatus.OK if flag else http.HTTPStatus.FORBIDDEN,
        )
