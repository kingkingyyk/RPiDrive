import json

from django.contrib.auth import authenticate
from django.contrib.auth import login as d_login
from django.contrib.auth import logout as d_logout
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from drive.utils.login_protect import LoginProtect
from django.views.decorators.csrf import csrf_exempt

from . import requires_admin, requires_login

@csrf_exempt
@require_http_methods(["POST"])
@LoginProtect.apply_login_protect
def login(request):
    data = json.loads(request.body)
    success = False
    username = data['u']
    password = data['p']
    user = authenticate(username=username, password=password)
    if user is not None:
        d_login(request, user)
        success = True
    return JsonResponse({'success': success}), success


@require_http_methods(["POST"])
@requires_login
def logout(request):
    d_logout(request)
    return JsonResponse({})


def current_user(request):
    data = {'loggedIn': request.user.is_authenticated}
    if data['loggedIn']:
        data['superuser'] = request.user.is_superuser
    return JsonResponse(data)


def serialize_user(user):
    return {'id': user.id, 'username': user.username, 'superuser': user.is_superuser}

@requires_admin
def list_users(request):
    users = User.objects.order_by('id').all()
    return JsonResponse({'values': [serialize_user(x) for x in users]})

@require_http_methods(["POST"])
@requires_admin
@transaction.atomic
def create_user(request):
    data = json.loads(request.body)
    if data.get('superuser', False):
        user = User.objects.create_superuser(username=data['u'],
                                            email=data['u']+'@rpidrive.com',
                                            password=data['p'])
    else:
        user = User.objects.create_user(username=data['u'],
                                        email=data['u']+'@rpidrive.com',
                                        password=data['p'])
    return JsonResponse(serialize_user(user))

@require_http_methods(["POST", "DELETE"])
@requires_admin
@transaction.atomic
def manage_user(request, user_id):
    user = User.objects.select_for_update().get(pk=user_id)
    if request.method == 'POST':
        data = json.loads(request.body)
        user.is_username = data['u']
        if data['p']:
            user.set_password(data['p'])
        user.is_superuser = data.get('superuser', False)
        user.save()
    else:
        user.delete()
    return JsonResponse({})
