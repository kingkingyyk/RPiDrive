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
                from drive.features.downloader import Downloader
                Downloader.start()

                from .utils.model_utils import ModelUtils
                ModelUtils.recursive_sync_folder()