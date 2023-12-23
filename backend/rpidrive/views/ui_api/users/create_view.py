import http

from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, EmailStr, ValidationError

from rpidrive.controllers.exceptions import NoPermissionException
from rpidrive.controllers.user import create_user
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    """Request model for view"""

    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    is_superuser: bool
    is_active: bool


class UserCreateView(LoginRequiredMixin, View):
    """Create user view"""

    @handle_exceptions(
        known_exc={
            IntegrityError,
            NoPermissionException,
            ValidationError,
        }
    )
    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        user = create_user(
            request.user,
            data.username,
            data.email,
            data.password,
            data.is_superuser,
            first_name=data.first_name,
            last_name=data.last_name,
        )
        return JsonResponse({"id": user.pk}, status=http.HTTPStatus.CREATED)
