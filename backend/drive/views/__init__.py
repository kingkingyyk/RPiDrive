from django.http.response import JsonResponse
from django.contrib.auth.models import User
from django.conf import settings

def get_user(request):
    if settings.DEBUG:
        return User.objects.filter(is_superuser=True).first()
    else:
        return request.user

def requires_login(function):
    def wrapper(request, *args, **kw):
        user=get_user(request)
        if settings.DEBUG or (user and user.is_authenticated):
            return function(request, *args, **kw)
        else:
            return JsonResponse({}, status=401)
    return wrapper

def requires_admin(function):
    def wrapper(request, *args, **kw):
        user=get_user(request)
        if settings.DEBUG or (user and user.is_superuser):
            return function(request, *args, **kw)
        else:
            return JsonResponse({}, status=401)
    return wrapper