from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.views import View
from pydantic import BaseModel, EmailStr, ValidationError

from rpidrive.controllers.exceptions import (
    InvalidOperationRequestException,
    NoPermissionException,
)
from rpidrive.controllers.user import (
    UserNotFoundException,
    delete_user,
    get_user,
    update_user,
)
from rpidrive.views.decorators.generics import handle_exceptions


class _RequestModel(BaseModel):
    """Request model for view"""

    email: EmailStr
    password: Optional[str] = None
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    is_superuser: bool
    is_active: bool


class UserDetailView(LoginRequiredMixin, View):
    """User detail view"""

    @handle_exceptions(
        known_exc={
            InvalidOperationRequestException,
            NoPermissionException,
            UserNotFoundException,
            ValidationError,
        }
    )
    def post(self, request, user_id: int, *args, **kwargs):
        """Handle POST request"""
        data = _RequestModel.model_validate_json(request.body)
        update_user(
            request.user,
            user_id,
            data.email,
            data.password,
            data.is_superuser,
            first_name=data.first_name,
            last_name=data.last_name,
            is_active=data.is_active,
        )
        return JsonResponse({})

    @handle_exceptions(
        known_exc={
            NoPermissionException,
            UserNotFoundException,
        }
    )
    def get(self, request, user_id: int, *_args, **_kwargs):
        """Handle GET request"""
        user = get_user(request.user, user_id)
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

    @handle_exceptions(
        known_exc={
            InvalidOperationRequestException,
            NoPermissionException,
            UserNotFoundException,
        }
    )
    def delete(self, request, user_id: int, *args, **kwargs) -> JsonResponse:
        """Handle DELETE request"""
        delete_user(request.user, user_id)
        return JsonResponse({})
