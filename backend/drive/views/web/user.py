import http
import json

from datetime import datetime
from typing import Optional

from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.db import transaction
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)
from pydantic import BaseModel, Field
from pydantic.error_wrappers import ValidationError

from drive.cache import ModelCache
from drive.views.web.shared import (
    catch_error,
    format_dt_iso,
    generate_error_response,
    login_required_401,
    requires_admin,
)

class UserCreationRequest(BaseModel):
    """Model for user creation request"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    isActive: bool
    isSuperuser: bool

class UserUpdateRequest(BaseModel):
    """Model for user update request"""
    username: str = Field(..., min_length=1)
    password: Optional[str]
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    isActive: bool
    isSuperuser: bool

class UserModel(BaseModel):
    """User serialization model"""
    id: int
    username: str
    firstName: Optional[str]
    lastName: Optional[str]
    email: Optional[str]
    isActive: bool
    isSuperuser: bool
    lastLogin: Optional[datetime]

def serialize_user(user: User, refresh_cache: bool=False):
    """Convert user object into dictionary"""
    if not ModelCache.exists(user) or refresh_cache:
        ModelCache.set(
            user,
            UserModel(
                id=user.pk,
                username=user.username,
                firstName=user.first_name,
                lastName=user.last_name,
                email=user.email,
                isActive=user.is_active,
                isSuperuser=user.is_superuser,
                lastLogin=format_dt_iso(user.last_login),
            ).dict()
        )
    return ModelCache.get(user)

@login_required_401
@requires_admin
@require_GET
def get_users(request):
    """Return all users"""
    users = User.objects.order_by('pk').all()
    return JsonResponse(dict(
        values=[serialize_user(x) for x in users]
    ))

@login_required_401
@requires_admin
@require_POST
@catch_error
def create_user(request):
    """Create user"""
    try:
        data = UserCreationRequest.parse_obj(
            json.loads(request.body))
    except json.decoder.JSONDecodeError:
        return generate_error_response('No data received.')
    except ValidationError:
        return generate_error_response('Invalid data received.')

    exists = User.objects.filter(username=data.username).exists()
    if exists:
        return generate_error_response('Username already exists.')

    user = User(
        username=data.username,
        first_name=data.firstName,
        last_name=data.lastName,
        email=data.email,
        is_active=data.isActive,
        is_superuser=data.isSuperuser,
        is_staff=data.isSuperuser,
    )
    user.set_password(data.password)
    user.save()
    return JsonResponse(
        serialize_user(user),
        status=http.HTTPStatus.CREATED
    )

@login_required_401
@require_GET
def get_current_user(request):
    """Return current user"""
    return JsonResponse(serialize_user(request.user))

@login_required_401
@requires_admin
@require_http_methods(['GET', 'POST', 'DELETE'])
@catch_error
def manage_user(request, user_id):
    """Get/update/delete user"""
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return generate_error_response('User not found.', status=http.HTTPStatus.NOT_FOUND)

    if request.method == 'GET':
        return JsonResponse(serialize_user(user))

    if request.method == 'POST':
        data = UserUpdateRequest.parse_obj(
            json.loads(request.body)
        )
        with transaction.atomic():
            if data.password:
                user.set_password(data.password)
                user.save()
            fields = dict(
                username=data.username,
                first_name=data.firstName,
                last_name=data.lastName,
                email=data.email,
                is_active=data.isActive,
                is_superuser=data.isSuperuser,
                is_staff=data.isSuperuser,
            )
            for key, value in fields.items():
                setattr(user, key, value)
            user.save(update_fields=list(fields.keys()))
        return JsonResponse(serialize_user(user, refresh_cache=True))

    if request.method == 'DELETE':
        ModelCache.clear(user)
        user.delete()
        return JsonResponse({})

    return JsonResponse({}, status=http.HTTPStatus.METHOD_NOT_ALLOWED)
