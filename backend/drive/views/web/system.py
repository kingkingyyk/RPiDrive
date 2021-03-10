import json
import os
import sys
import time
import uuid
import psutil
from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
from drive.core.storage_provider import create_storage_provider_helper
from drive.models import System
from drive.views.web.shared import generate_error_response, requires_admin
from drive.views.web.storage_provider import StorageProviderRequest
from drive.utils.indexer import LocalStorageProviderIndexer

class InitializeSystemRequest:
    """InitializeSystem request keys"""
    INIT_KEY = 'initKey'
    STORAGE_PROVIDER_KEY = 'storageProvider'
    USER_KEY = 'user'

class CreateUserRequest:
    """Create user request keys"""
    USERNAME_KEY = 'username'
    PASSWORD_KEY = 'password'
    FIRST_NAME_KEY = 'firstName'
    LAST_NAME_KEY = 'lastName'
    EMAIL_KEY = 'email'
    ACTIVE_KEY = 'isActive'
    SUPERUSER_KEY = 'isSuperuser'

# pylint: disable=too-many-return-statements
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def initialize_system(request):
    """Initialize system"""
    system, created = System.objects.get_or_create()
    if created:
        system.init_key = str(uuid.uuid4())
        system.save()
        print('Initialization Key : {}'.format(system.init_key))
    if request.method == 'GET':
        if not system.initialized:
            return JsonResponse({}, status=200)
        return generate_error_response('', status=401)
    if request.method == 'POST':
        if system.initialized:
            return generate_error_response('System has already been initialized!')
        data = json.loads(request.body)
        if data[InitializeSystemRequest.INIT_KEY] != system.init_key:
            return generate_error_response(
                'Invalid initialization key! Please check server console.',
                status=401)

        with transaction.atomic():
            # Create superuser
            user_data = data[InitializeSystemRequest.USER_KEY]
            user = User(username=user_data[CreateUserRequest.USERNAME_KEY],
                 first_name=user_data[CreateUserRequest.FIRST_NAME_KEY],
                 last_name=user_data[CreateUserRequest.LAST_NAME_KEY],
                 email=user_data[CreateUserRequest.EMAIL_KEY],
                 is_active=user_data[CreateUserRequest.ACTIVE_KEY],
                 is_staff=True,
                 is_superuser=user_data[CreateUserRequest.SUPERUSER_KEY])
            user.set_password(user_data[CreateUserRequest.PASSWORD_KEY])
            user.save()

            # Create storage provider
            sp_data = data[InitializeSystemRequest.STORAGE_PROVIDER_KEY]
            try:
                StorageProviderRequest.inspect_create_data(sp_data)
            except Exception as e: # pylint: disable=broad-except, invalid-name
                return generate_error_response(str(e))

            # pylint: disable=unused-variable
            s_p, file_obj = create_storage_provider_helper(
                name=sp_data[StorageProviderRequest.NAME_KEY],
                sp_type=sp_data[StorageProviderRequest.TYPE_KEY],
                path=sp_data[StorageProviderRequest.PATH_KEY])

            # Flag system as initialized
            System.objects.update(initialized=True)

        LocalStorageProviderIndexer.sync(file_obj, True)
        return JsonResponse({}, status=200)
    return JsonResponse({}, status=405)

@login_required
@requires_admin
@require_GET
def get_network_info(request):
    """Return network info"""
    before = psutil.net_io_counters()
    time.sleep(1.0)
    after = psutil.net_io_counters()
    ret_value = {
        'downloadSpeed': after.bytes_recv - before.bytes_recv,
        'uploadSpeed': after.bytes_sent - before.bytes_sent,
        'downloadTotal': after.bytes_recv,
        'uploadTotal': after.bytes_sent
    }
    return JsonResponse(ret_value)

@login_required
@requires_admin
@require_GET
def get_system_info(request):
    """Return system info"""
    def disk_usage_to_dict(path):
        disk_usage = psutil.disk_usage(path)
        return {
            'total': disk_usage.total,
            'used': disk_usage.used,
            'free': disk_usage.free,
            'percent': disk_usage.percent
        }

    mem = psutil.virtual_memory()
    os_info = os.uname()
    ret_value = {
        'cpuCount': psutil.cpu_count(),
        'cpuFrequency': psutil.cpu_freq().current,
        'cpuUsage': psutil.cpu_percent(),
        'memTotal': mem.total,
        'memUsed': mem.used,
        'memUsage': mem.percent,
        'disks': [
            {**{'path': x.mountpoint}, **disk_usage_to_dict(x.mountpoint)}
            for x in psutil.disk_partitions() if x.device.startswith('/dev/sd')
        ],
        'osName': '{}-{}-{}'.format(os_info.sysname, os_info.release, os_info.version),
        'osArch': os_info.machine,
        'pythonVersion': sys.version

    }
    return JsonResponse(ret_value)
