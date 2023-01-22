import http
import json
import os
import sys
import time
import uuid

import psutil

from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth.models import User
from django.db import transaction
from pydantic import BaseModel, Field

from drive.core.storage_provider import create_storage_provider_helper
from drive.models import System
from drive.views.web.shared import (
    catch_error,
    generate_error_response,
    login_required_401,
    requires_admin,
)
from drive.views.web.storage_provider import StorageProviderCreationRequestModel

class UserCreationRequest(BaseModel):
    """Create user request"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)

class InitializeSystemRequest(BaseModel):
    """InitializeSystem request"""
    initKey: str = Field(..., min_length=1)
    storageProvider: StorageProviderCreationRequestModel
    user: UserCreationRequest

# pylint: disable=too-many-return-statements
@csrf_exempt
@require_http_methods(['GET', 'POST'])
@catch_error
def initialize_system(request):
    """Initialize system"""
    system, created = System.objects.get_or_create()
    if created:
        system.init_key = str(uuid.uuid4())
        system.save()
        print(f'Initialization Key : {system.init_key}')

    if request.method == 'GET':
        if not system.initialized:
            return JsonResponse({}, status=http.HTTPStatus.OK)
        return generate_error_response(
            '', status=http.HTTPStatus.UNAUTHORIZED
        )

    if request.method == 'POST':
        if system.initialized:
            return generate_error_response(
                'System has already been initialized!'
            )
        data = InitializeSystemRequest.parse_obj(json.loads(request.body))
        if data.initKey != system.init_key:
            return generate_error_response(
                'Invalid initialization key! Please check server console.',
                status=http.HTTPStatus.UNAUTHORIZED
            )
        data.storageProvider.validate_fields()

        with transaction.atomic():
            # Create superuser
            user = User(
                username=data.user.username,
                first_name=data.user.firstName,
                last_name=data.user.lastName,
                email=data.user.email,
                is_active=True,
                is_staff=True,
                is_superuser=True,
            )
            user.set_password(data.user.password)
            user.save()

            # Create storage provider
            create_storage_provider_helper(
                name=data.storageProvider.name,
                sp_type=data.storageProvider.type,
                path=data.storageProvider.path,
            )

            # Flag system as initialized
            System.objects.update(initialized=True)
        return JsonResponse({}, status=http.HTTPStatus.OK)

    return JsonResponse({}, status=http.HTTPStatus.METHOD_NOT_ALLOWED)

@login_required_401
@requires_admin
@require_GET
@catch_error
def get_network_info(request):
    """Return network info"""
    before = psutil.net_io_counters()
    time.sleep(1.0)
    after = psutil.net_io_counters()
    ret_value = dict(
        downloadSpeed=after.bytes_recv - before.bytes_recv,
        uploadSpeed=after.bytes_sent - before.bytes_sent,
        downloadTotal=after.bytes_recv,
        uploadTotal=after.bytes_sent,
    )
    return JsonResponse(ret_value)

@login_required_401
@requires_admin
@require_GET
@catch_error
def get_system_info(request):
    """Return system info"""
    def disk_usage_to_dict(path):
        disk_usage = psutil.disk_usage(path)
        return dict(
            total=disk_usage.total,
            used=disk_usage.used,
            free=disk_usage.free,
            percent=disk_usage.percent,
        )

    mem = psutil.virtual_memory()
    os_info = os.uname()
    ret_value = dict(
        cpuCount=psutil.cpu_count(),
        cpuFrequency=int(psutil.cpu_freq().current),
        cpuUsage=psutil.cpu_percent(),
        memTotal=mem.total,
        memUsed=mem.used,
        memUsage=mem.percent,
        disks=[
            {
                **{'path': x.mountpoint},
                **disk_usage_to_dict(x.mountpoint)
            }
            for x in psutil.disk_partitions()\
            if x.device.startswith('/dev/sd')
        ],
        osName=f'{os_info.sysname}-{os_info.release}-{os_info.version}',
        osArch=os_info.machine,
        pythonVersion=sys.version,

    )
    return JsonResponse(ret_value)
