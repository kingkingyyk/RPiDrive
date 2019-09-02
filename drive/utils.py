import os, re, shutil, stat

# https://stackoverflow.com/questions/33208849/python-django-streaming-video-mp4-file-using-httpresponse/33964547

range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)

class RangeFileWrapper(object):
    def __init__(self, filelike, chunk_size=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.chunk_size = chunk_size

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            data = self.filelike.read(self.chunk_size)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()
            data = self.filelike.read(min(self.remaining, self.chunk_size))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data
        
        
class FileUtils:
    
    @staticmethod
    def delete_dir(top, delete_root=True, best_effort=False):
        if os.path.exists(top):
            #Unlink symbolic linked files/folders
            for root, dirs, files in os.walk(top, topdown=False):
                for name in [x for x in files+dirs if os.path.islink(os.path.join(root, x))]:
                    os.unlink(os.path.join(root, name))

            for root, dirs, files in os.walk(top, topdown=False):
                for name in files:
                    FileUtils.delete_file_or_dir(os.path.join(root, name), best_effort)
                for name in dirs:
                    FileUtils.delete_file_or_dir(os.path.join(root, name), best_effort)

            if delete_root:
                FileUtils.delete_file_or_dir(top, best_effort)

    @staticmethod
    def delete_file_or_dir(top, best_effort=False):
        if os.path.exists(top):
            if os.path.islink(top):
                if best_effort:
                    try:
                        os.unlink(top)
                    except:
                        pass
                else:
                    os.unlink(top)

        if os.path.exists(top):
            if os.path.isfile(top):
                if best_effort:
                    try:
                        os.chmod(top, stat.S_IWRITE)
                        os.remove(top)
                    except:
                        pass
                else:
                    os.chmod(top, stat.S_IWRITE)
                    os.remove(top)
            else:
                shutil.rmtree(top, ignore_errors=best_effort)


from datetime import datetime, timedelta
from django.http.response import HttpResponseForbidden
from django.utils.timezone import get_current_timezone
from rpidrive.settings import LOGIN_ATTEMPT_LIMIT, LOGIN_ATTEMPT_TIMEOUT


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
            if request.method == 'POST':
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
                        if LoginProtect.ip_login_count[ip] >= LOGIN_ATTEMPT_LIMIT:
                            LoginProtect.next_available_login[ip] = datetime.now(tz=get_current_timezone()) + timedelta(seconds=LOGIN_ATTEMPT_TIMEOUT)
                    return auth_data
            return func(request)[0]
        return verify


