from django.http.response import JsonResponse
from django.contrib.auth import login, logout, authenticate
from .shared import generate_error_response
from django.views.decorators.http import require_GET, require_POST, require_http_methods
import json

@require_GET
def is_logged_in(request):
    return JsonResponse({'result': request.user.is_authenticated})

@require_POST
def user_login(request):
    data = json.loads(request.body)
    username = data['username']
    password = data['password']
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        return JsonResponse({}, status=200)
    return generate_error_response('', status=401)

@require_POST
def user_logout(request):
    logout(request)
    return JsonResponse({})
