import os
import sys
import time
from typing import List

import cpuinfo
import psutil

from django.contrib.auth.models import User
from pydantic import BaseModel

from rpidrive.controllers.exceptions import NoPermissionException


class CPUInfo(BaseModel):
    """Cpu info model"""

    model: str
    cores: int
    frequency: int
    usage: float


class MemoryInfo(BaseModel):
    """Memory info model"""

    total: int
    used: int
    usage: float


class DiskInfo(BaseModel):
    """Disk model"""

    name: str
    total: int
    used: int
    free: int
    percent: float


class Environment(BaseModel):
    """Environment model"""

    os: str
    arch: str
    python: str


class Network(BaseModel):
    """Network model"""

    download_speed: int
    upload_speed: int
    downloads: int
    uploads: int


def get_cpu_info(user: User) -> CPUInfo:
    """Returns cpu info"""
    if not user.is_superuser:
        raise NoPermissionException()
    return CPUInfo(
        model=cpuinfo.get_cpu_info()["brand_raw"],
        cores=psutil.cpu_count(),
        frequency=int(psutil.cpu_freq().current),
        usage=psutil.cpu_percent(),
    )


def get_mem_info(user: User) -> MemoryInfo:
    """Returns memory info"""
    if not user.is_superuser:
        raise NoPermissionException()
    mem = psutil.virtual_memory()
    return MemoryInfo(
        total=mem.total,
        used=mem.used,
        usage=mem.percent,
    )


def get_disk_info(user: User) -> List[DiskInfo]:
    """Return disk info"""
    if not user.is_superuser:
        raise NoPermissionException()
    partitions = [
        x
        for x in psutil.disk_partitions()
        if x.device.startswith("/dev/hd")
        or x.device.startswith("/dev/sd")
        or x.device.startswith("/dev/nvme")
    ]
    info_list = []
    for partition in partitions:
        disk_usage = psutil.disk_usage(partition.mountpoint)
        info_list.append(
            DiskInfo(
                name=partition.mountpoint,
                total=disk_usage.total,
                used=disk_usage.used,
                free=disk_usage.free,
                percent=disk_usage.percent,
            )
        )
    return info_list


def get_environ_info(user: User) -> Environment:
    """Returns environment info"""
    if not user.is_superuser:
        raise NoPermissionException()
    os_info = os.uname()
    return Environment(
        os=f"{os_info.sysname}-{os_info.release}-{os_info.version}",
        arch=os_info.machine,
        python=sys.version,
    )


def get_network_info(user: User) -> Network:
    """Returns network info"""
    if not user.is_superuser:
        raise NoPermissionException()
    before = psutil.net_io_counters()
    time.sleep(1.0)
    after = psutil.net_io_counters()
    return Network(
        download_speed=after.bytes_recv - before.bytes_recv,
        upload_speed=after.bytes_sent - before.bytes_sent,
        downloads=after.bytes_recv,
        uploads=after.bytes_sent,
    )
