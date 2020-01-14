from django.apps import AppConfig
import sys


class DriveConfig(AppConfig):
    name = 'drive'
    ready_executed = False

    def ready(self):
        if not self.ready_executed:
            self.ready_executed = True
            import drive.signals

            if sys.argv[1] not in ['migrate', 'makemigrations', 'createsuperuser']:
                from .utils.model_utils import ModelUtils
                ModelUtils.auto_create_drive()
                ModelUtils.recursive_sync_folder(True)

                from drive.features.downloader import Downloader
                Downloader.start_run()

                from .features.file_sync import FileSyncDaemon
                FileSyncDaemon.start_run()

