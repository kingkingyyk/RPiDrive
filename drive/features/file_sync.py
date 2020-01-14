from ..models import *
from ..utils.utils import Utils
from threading import Thread
from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone
import time


class FileSyncDaemon(Thread):

    def run(self):
        while True:
            now = datetime.now(tz=get_current_timezone())
            next = Synchronizer.objects.first().next_sync_time
            if next and now > next:
                if Storage.objects.filter(primary=True).count() > 0 and Storage.objects.filter(primary=False).count() > 0:
                    primary = Storage.objects.get(primary=True)
                    for secondary in Storage.objects.filter(primary=False).all():
                        secondary.is_synching = True
                        secondary.save()
                        rc, stdout, stderr = Utils.invoke_command(['rsync', '-a', '--delete', primary.base_path, secondary.base_path])
                        secondary.is_synching = False
                        secondary.last_sync_status = datetime.now() + '\n' + stdout + '\n' + stderr
                        if rc:
                            secondary.last_sync_time = datetime.now()
                        secondary.save()

                sync = Synchronizer.objects.first()
                if not sync.day_mask:
                    sync.next_sync_time = None
                else:
                    sync.next_sync_time = now + timedelta(minutes=sync.period)
                    sync.next_sync_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    if not sync.can_run_on_day(sync.next_sync_time):
                        while not sync.can_run_on_day(sync.next_sync_time):
                            sync.next_sync_time = sync.next_sync_time + timedelta(days=sync.period)
                sync.save()

            time.sleep(5.0)

    @staticmethod
    def start_run():
        if Synchronizer.objects.count() == 0:
            Synchronizer(next_sync_time=datetime.now()).save()

        d = FileSyncDaemon()
        d.daemon = True
        d.start()