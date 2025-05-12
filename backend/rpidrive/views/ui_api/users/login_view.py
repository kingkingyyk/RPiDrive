import http

from django.contrib.auth import login, authenticate
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, ValidationError

from rpidrive.views.decorators.generics import handle_exceptions
from rpidrive.views.decorators.mixins import BruteForceProtectMixin


class _RequestModel(BaseModel):
    """Request model for login"""

    username: str
    password: str


class UserLoginView(BruteForceProtectMixin, View):
    """User login view"""

    @handle_exceptions(known_exc={ValidationError})
    def post(self, request, *_args, **_kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        user = authenticate(
            username=data.username,
            password=data.password,
        )
        if user:
            login(request, user)
            return JsonResponse({})

        return JsonResponse(
            {"error": "Invalid username/password"},
            status=http.HTTPStatus.UNAUTHORIZED,
        )
