from datetime import datetime, timedelta
from django.http.response import HttpResponseForbidden
from django.utils.timezone import get_current_timezone
from django.conf import settings


class LoginProtect:
    ip_login_count = {}
    next_available_login = {}

    @staticmethod
    def _get_request_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def apply_login_protect(func):
        def verify(request):
            if settings.LOGIN_ATTEMPT_LIMIT > 0 and request.method == 'POST':
                ip = LoginProtect._get_request_ip(request)
                next_available_time = LoginProtect.next_available_login.get(ip, datetime.now(tz=get_current_timezone()) - timedelta(seconds=1))
                if next_available_time > datetime.now(tz=get_current_timezone()):
                    return HttpResponseForbidden('<html><h2>Too many login failures</h2><h5>Please try again later!!</h5></html>')
                else:
                    auth_data, auth_success = func(request)
                    if auth_success:
                        if ip in LoginProtect.next_available_login:
                            LoginProtect.next_available_login.pop(ip)
                        if ip in LoginProtect.ip_login_count:
                            LoginProtect.ip_login_count.pop(ip)
                    else:
                        LoginProtect.ip_login_count[ip] = LoginProtect.ip_login_count.get(ip, 0) + 1
                        if LoginProtect.ip_login_count[ip] >= settings.LOGIN_ATTEMPT_LIMIT:
                            LoginProtect.next_available_login[ip] = datetime.now(tz=get_current_timezone()) + timedelta(seconds=settings.LOGIN_ATTEMPT_TIMEOUT)
                    return auth_data
            return func(request)[0]
        return verify


