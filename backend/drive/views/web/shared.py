import http
import json
import logging
import traceback

from datetime import datetime, timedelta
from functools import wraps

import redis

from django.contrib.auth.models import User
from django.http.response import JsonResponse, HttpResponse
from django.conf import settings
from pydantic.error_wrappers import ValidationError

from drive.models import StorageProvider, StorageProviderUser

_REDIS_POOL = None

def get_redis_pool():
    """Get redis pool object"""
    global _REDIS_POOL # pylint: disable=global-statement
    if not _REDIS_POOL:
        _REDIS_POOL = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
    return _REDIS_POOL

def generate_error_response(msg, status=http.HTTPStatus.BAD_REQUEST):
    """Return a json response with error message"""
    return JsonResponse(dict(error=str(msg)), status=status)

def catch_error(func):
    """Wrap method and return error if exception raised"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as exc:
            return generate_error_response(
                exc, status=http.HTTPStatus.BAD_REQUEST
            )
        except Exception as exc: # pylint: disable=broad-except
            exc_trace = traceback.format_exc()
            logging.error(exc)
            return generate_error_response(
                exc_trace.splitlines()[-1],
                status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            )
    return wrapper

def spam_protect(func):
    """For wrapping method to block brute force attack"""
    def wrapper(request, *args, **kwargs): # pylint: disable=unused-argument
        remote_addr = None
        if settings.REVERSE_PROXY_IP_HEADER:
            remote_addr = request.META.get(
                settings.REVERSE_PROXY_IP_HEADER
            ).split(',')[0]
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
                    return generate_error_response(
                        error_text,
                        http.HTTPStatus.FORBIDDEN,
                    )
                return HttpResponse(
                    f'<html>{error_text}</html>',
                    status=http.HTTPStatus.FORBIDDEN,
                )
        result = func(request)
        if http.HTTPStatus.OK <= result.status_code < 300:
            r_dict.delete(remote_addr)
        elif result.status_code in {
                    http.HTTPStatus.UNAUTHORIZED,
                    http.HTTPStatus.FORBIDDEN,
                    http.HTTPStatus.NOT_FOUND
                }:
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
                    remote_profile['nextAllowedTime']
                )

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
        return generate_error_response(
            'No permission to perform required action',
            status=http.HTTPStatus.UNAUTHORIZED,
        )
    return wrapper

def get_storage_provider_permission(s_p: StorageProvider, user: User):
    """Return storage provider permission of user"""
    perm = s_p.storageprovideruser_set.filter(user=user).first()
    return StorageProviderUser.PERMISSION.NONE if not perm else perm.permission

def has_storage_provider_permission(s_p: StorageProvider, user: User, required_level: int):
    """Return user has enough permission on storage provider"""
    return user.is_superuser or get_storage_provider_permission(s_p, user) >= required_level

def user_passes_test(test_func):
    """Decorator for views that checks that the user passes the given test"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return generate_error_response(
                'Unauthorized',
                http.HTTPStatus.UNAUTHORIZED,
            )
        return _wrapped_view
    return decorator

def login_required_401(function=None):
    """Decorator for returning 401 when not authenticated"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def format_dt_iso(d_t: datetime) -> str:
    """Convert datetime to isoformat"""
    return d_t.replace(microsecond=0).isoformat().replace('+00:00', 'Z')\
            if d_t else None
