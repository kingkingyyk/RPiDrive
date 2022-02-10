import json
import logging
import traceback
from datetime import datetime, timedelta
import redis
from django.contrib.auth.models import User
from django.http.response import JsonResponse, HttpResponse
from django.conf import settings
from drive.models import StorageProvider, StorageProviderUser

_REDIS_POOL = None

def get_redis_pool():
    """Get redis pool object"""
    global _REDIS_POOL # pylint: disable=global-statement
    if not _REDIS_POOL:
        _REDIS_POOL = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB)
    return _REDIS_POOL

def generate_error_response(msg, status=400):
    """Return a json response with error message"""
    return JsonResponse({'error': msg}, status=status)


def catch_error(func):
    """Wrap method and return error if exception raised"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exp: # pylint: disable=broad-except
            logging.error(traceback.format_exc())
            return generate_error_response(str(exp), status=500)
    return wrapper

def spam_protect(func):
    """For wrapping method to block brute force attack"""
    def wrapper(request, *args, **kwargs): # pylint: disable=unused-argument
        remote_addr = None
        if settings.REVERSE_PROXY_IP_HEADER:
            remote_addr = request.META.get(settings.REVERSE_PROXY_IP_HEADER).split(',')[0]
        else:
            remote_addr = request.META.get('REMOTE_ADDR')

        r_dict = redis.Redis(connection_pool=get_redis_pool())
        remote_profile_str = r_dict.get(remote_addr)
        if remote_profile_str:
            remote_profile = json.loads(remote_profile_str)
            next_allowed_time = remote_profile.get('nextAllowedTime', None)
            if next_allowed_time:
                next_allowed_time = datetime.fromisoformat(next_allowed_time)
            if next_allowed_time and next_allowed_time > datetime.now():
                error_text = 'Request blocked temporarily due to too many failed attempts!'
                if request.content_type == 'application/json':
                    return JsonResponse(
                        dict(error=error_text),
                        status=403)
                return HttpResponse(f'<html>{error_text}</html>', status=403)
        result = func(request)
        if 200 <= result.status_code < 300:
            r_dict.delete(remote_addr)
        elif result.status_code in {401, 403, 404}:
            if remote_profile_str:
                remote_profile = json.loads(remote_profile_str)
            else:
                remote_profile = {'failureCount': 0}
            remote_profile['failureCount'] += 1
            if remote_profile['failureCount'] >= settings.SPAM_MAX_RETRIES:
                remote_profile['nextAllowedTime'] = (datetime.now() + \
                    timedelta(seconds=settings.SPAM_BLOCK_DURATION)).isoformat()
                logging.warning(
                    'Blocked %s until %s.',
                    remote_addr,
                    remote_profile['nextAllowedTime'])

            remote_profile_str = json.dumps(remote_profile)
            def save(pipe: redis.client.Pipeline):
                pipe.set(remote_addr, remote_profile_str)

            r_dict.transaction(save)
        return result
    return wrapper

def reset_spam_protect():
    """For resetting login block"""
    r_dict = redis.Redis(connection_pool=get_redis_pool())
    r_dict.flushdb()

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
