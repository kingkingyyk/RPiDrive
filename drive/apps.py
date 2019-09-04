from django.apps import AppConfig
import sys


class DriveConfig(AppConfig):
    name = 'drive'
    executed = False

    def ready(self):
        from .downloader import Downloader

        if not self.executed and sys.argv[1] not in ['migrate', 'makemigrations']:
            Downloader.start()
            self.executed = True
