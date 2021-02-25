from django.http.response import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
import redis
import logging
import json
import traceback


LOGGER = logging.getLogger(__name__)

def generate_error_response(msg, status=400):
    return JsonResponse({'error': msg}, status=status)


def catch_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exp:
            LOGGER.error(traceback.format_exc())
            return generate_error_response(str(exp), status=500)
    return wrapper

def login_protect(func):
    def wrapper(request):
        remote_addr = None
        if settings.REVERSE_PROXY_IP_HEADER:
            remote_addr = request.META.get(settings.REVERSE_PROXY_IP_HEADER).split(',')[0]
        else:
            remote_addr = request.META.get('REMOTE_ADDR')

        pool = redis.ConnectionPool(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT,
                                    db=settings.REDIS_DB)
        r = redis.Redis(connection_pool=pool)
        remote_profile_str = r.get(remote_addr)
        if remote_profile_str:
            remote_profile = json.loads(remote_profile_str)
            next_allowed_time = remote_profile.get('nextAllowedTime', None)
            if next_allowed_time:
                next_allowed_time = datetime.fromisoformat(next_allowed_time)
            if next_allowed_time and next_allowed_time > datetime.now():
                return JsonResponse({'error': 'Login blocked temporarily due to too many failed attempts!'}, status=403)
        result = func(request)
        if result.status_code == 200:
            r.delete(remote_addr)
        else:
            if remote_profile_str:
                remote_profile = json.loads(remote_profile_str)
            else:
                remote_profile = {'failureCount': 0}
            remote_profile['failureCount'] += 1
            if remote_profile['failureCount'] >= settings.LOGIN_MAX_RETRIES:
                remote_profile['nextAllowedTime'] = (datetime.now() + timedelta(seconds=settings.LOGIN_BLOCK_DURATION)).isoformat()
            
            remote_profile_str = json.dumps(remote_profile)
            def save(pipe: redis.client.Pipeline):
                pipe.set(remote_addr, remote_profile_str)

            r.transaction(save)
        return result
    return wrapper

def requires_admin(func):
    def wrapper(request, *args, **kw):
        user=request.user
        if user and user.is_superuser:
            return func(request, *args, **kw)
        else:
            return generate_error_response('No permission to perform required action', status=401)
    return wrapper
