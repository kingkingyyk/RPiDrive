import json
import logging
import traceback
from datetime import datetime, timedelta
import redis
from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.conf import settings
from drive.models import StorageProvider, StorageProviderUser


LOGGER = logging.getLogger(__name__)

def generate_error_response(msg, status=400):
    """Return a json response with error message"""
    return JsonResponse({'error': msg}, status=status)


def catch_error(func):
    """Wrap method and return error if exception raised"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exp: # pylint: disable=broad-except
            LOGGER.error(traceback.format_exc())
            return generate_error_response(str(exp), status=500)
    return wrapper

def login_protect(func):
    """For wrapping login method to block brute force attack"""
    def wrapper(request):
        remote_addr = None
        if settings.REVERSE_PROXY_IP_HEADER:
            remote_addr = request.META.get(settings.REVERSE_PROXY_IP_HEADER).split(',')[0]
        else:
            remote_addr = request.META.get('REMOTE_ADDR')

        pool = redis.ConnectionPool(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT,
                                    db=settings.REDIS_DB)
        r_dict = redis.Redis(connection_pool=pool)
        remote_profile_str = r_dict.get(remote_addr)
        if remote_profile_str:
            remote_profile = json.loads(remote_profile_str)
            next_allowed_time = remote_profile.get('nextAllowedTime', None)
            if next_allowed_time:
                next_allowed_time = datetime.fromisoformat(next_allowed_time)
            if next_allowed_time and next_allowed_time > datetime.now():
                return JsonResponse(
                    {'error': 'Login blocked temporarily due to too many failed attempts!'},
                    status=403)
        result = func(request)
        if result.status_code == 200:
            r_dict.delete(remote_addr)
        else:
            if remote_profile_str:
                remote_profile = json.loads(remote_profile_str)
            else:
                remote_profile = {'failureCount': 0}
            remote_profile['failureCount'] += 1
            if remote_profile['failureCount'] >= settings.LOGIN_MAX_RETRIES:
                remote_profile['nextAllowedTime'] = (datetime.now() + \
                    timedelta(seconds=settings.LOGIN_BLOCK_DURATION)).isoformat()

            remote_profile_str = json.dumps(remote_profile)
            def save(pipe: redis.client.Pipeline):
                pipe.set(remote_addr, remote_profile_str)

            r_dict.transaction(save)
        return result
    return wrapper

def requires_admin(func):
    """Wrapper for method that request admin privilege"""
    def wrapper(request, *args, **kw):
        user=request.user
        if user and user.is_superuser:
            return func(request, *args, **kw)
        return generate_error_response('No permission to perform required action', status=401)
    return wrapper

def get_storage_provider_permission(s_p: StorageProvider, user: User):
    """Return storage provider permission of user"""
    perm = s_p.storageprovideruser_set.filter(user=user).first()
    return StorageProviderUser.PERMISSION.NONE if not perm else perm.permission

def has_storage_provider_permission(s_p: StorageProvider, user: User, required_level: int):
    """Return user has enough permission on storage provider"""
    return user.is_superuser or get_storage_provider_permission(s_p, user) >= required_level
