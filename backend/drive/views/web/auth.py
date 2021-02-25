from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .shared import generate_error_response, login_protect
import json

@require_GET
def is_logged_in(request):
    flag = request.user.is_authenticated
    return JsonResponse({'result': flag}, status=200 if flag else 403)

@csrf_exempt
@login_protect
@require_POST
def user_login(request):
    data = json.loads(request.body)
    username = data['username']
    password = data['password']
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        return JsonResponse({}, status=200)
    return generate_error_response('Invalid username/password', status=401)

@login_required()
@require_POST
def user_logout(request):
    logout(request)
    response = JsonResponse({})
    response.delete_cookie('csrftoken')
    return response
