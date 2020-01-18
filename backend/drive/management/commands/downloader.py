from django.core.management.base import BaseCommand, CommandError
from drive.models import Storage
from threading import Thread

class Command(BaseCommand):
    help = 'Run downloader service'

    def handle(self, *args, **options):
        pass


class DownloaderThread(Thread):
    pass