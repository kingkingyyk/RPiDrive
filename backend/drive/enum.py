from enum import Enum
from datetime import timedelta
import humanize

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
             'Friday', 'Saturday', 'Sunday', ]

storage_sync_period = (15, 30, 60, 2*60, 4*60, 8*60, 12*60, 24*60)
storage_sync_period = {humanize.naturaldelta(timedelta(minutes=x)):x for x in storage_sync_period}


class PermissionType(Enum):
    read = 'READ'
    update = 'UPDATE'
    delete = 'DELETE'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class DownloadStatus(Enum):
    queue = 'In queue'
    downloading = 'Downloading'
    finished = 'Finished'
    paused = 'Paused'
    error = 'Error'
    stopped = 'Stopped'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)