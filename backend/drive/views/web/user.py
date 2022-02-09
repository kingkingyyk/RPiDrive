import json
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from drive.views.web.shared import generate_error_response, requires_admin


class UserRequest:
    """List of key in user request"""
    ID_KEY = 'id'
    USERNAME_KEY = 'username'
    PASSWORD_KEY = 'password'
    FIRST_NAME_KEY = 'firstName'
    LAST_NAME_KEY = 'lastName'
    EMAIL_KEY = 'email'
    IS_ACTIVE_KEY = 'isActive'
    IS_SUPERUSER_KEY = 'isSuperuser'
    LAST_LOGIN_KEY = 'lastLogin'

def serialize_user(user: User):
    """Convert user object into dictionary"""
    data = {
        UserRequest.ID_KEY: user.pk,
        UserRequest.USERNAME_KEY: user.username,
        UserRequest.FIRST_NAME_KEY: user.first_name,
        UserRequest.LAST_NAME_KEY: user.last_name,
        UserRequest.EMAIL_KEY: user.email,
        UserRequest.IS_ACTIVE_KEY: user.is_active,
        UserRequest.IS_SUPERUSER_KEY: user.is_superuser,
        UserRequest.LAST_LOGIN_KEY: user.last_login,
    }
    return data

@login_required()
@requires_admin
@require_GET
def get_users(request):
    """Return all users"""
    users = User.objects.all()
    return JsonResponse({'values': [serialize_user(x) for x in users]})

@login_required()
@requires_admin
@require_POST
def create_user(request):
    """Create user"""
    data = json.loads(request.body)
    user = User(
        username=data[UserRequest.USERNAME_KEY],
        first_name=data.get(UserRequest.FIRST_NAME_KEY, None),
        last_name=data.get(UserRequest.LAST_NAME_KEY, None),
        email=data.get(UserRequest.EMAIL_KEY, None),
        is_active=data[UserRequest.IS_ACTIVE_KEY],
        is_superuser=data[UserRequest.IS_SUPERUSER_KEY],
        is_staff=data[UserRequest.IS_SUPERUSER_KEY]
    )
    user.set_password(data[UserRequest.PASSWORD_KEY])
    user.save()
    return JsonResponse(serialize_user(user))

@login_required()
@require_GET
def get_current_user(request):
    """Return current user"""
    user = request.user
    return JsonResponse(serialize_user(user))

@login_required()
@requires_admin
@require_http_methods(['GET', 'POST', 'DELETE'])
def manage_user(request, user_id):
    """Get/update/delete user"""
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return generate_error_response('User not found', status=404)
    if request.method == 'GET':
        return JsonResponse(serialize_user(user))
    if request.method == 'POST':
        data = json.loads(request.body)
        with transaction.atomic():
            if data.get(UserRequest.PASSWORD_KEY, None):
                user.set_password(data[UserRequest.PASSWORD_KEY])
                user.save()
            User.objects.filter(pk=user_id).update(
                username=data[UserRequest.USERNAME_KEY],
                first_name=data[UserRequest.FIRST_NAME_KEY],
                last_name=data[UserRequest.LAST_NAME_KEY],
                email=data[UserRequest.EMAIL_KEY],
                is_active=data[UserRequest.IS_ACTIVE_KEY],
                is_superuser=data[UserRequest.IS_SUPERUSER_KEY],
                is_staff=data[UserRequest.IS_SUPERUSER_KEY]
            )
        user = User.objects.get(pk=user_id)
        return JsonResponse(serialize_user(user))
    if request.method == 'DELETE':
        user.delete()
        return JsonResponse({})
    return JsonResponse({}, status=405)
