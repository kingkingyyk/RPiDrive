import http
import json

from django.contrib.auth import login, logout, authenticate
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from pydantic import BaseModel

from drive.views.web.shared import (
    catch_error,
    generate_error_response,
    login_required_401,
    spam_protect,
)

class LoginModel(BaseModel):
    """Login Request Model"""
    username: str
    password: str

@require_GET
def is_logged_in(request):
    """Return is logged in"""
    flag = request.user.is_authenticated
    return JsonResponse(
        dict(result=flag),
        status=http.HTTPStatus.OK if flag else http.HTTPStatus.FORBIDDEN
    )

@csrf_exempt
@spam_protect
@require_POST
@catch_error
def user_login(request):
    """Perform login"""
    data = LoginModel.parse_obj(json.loads(request.body))
    user = authenticate(
        username=data.username,
        password=data.password
    )
    if user:
        login(request, user)
        return JsonResponse({}, status=http.HTTPStatus.OK)
    return generate_error_response(
        'Invalid username/password',
        status=http.HTTPStatus.UNAUTHORIZED
    )

@login_required_401
@require_POST
def user_logout(request):
    """Perform logout"""
    logout(request)
    response = JsonResponse({})
    response.delete_cookie('csrftoken')
    return response
