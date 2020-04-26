from django.core.management.base import BaseCommand, CommandError
from drive.models import Storage
from django.contrib.auth.models import User
from django.conf import settings
from drive.views.views_downloader import update_disk_cache

class Command(BaseCommand):
    help = 'Run initialization'

    def handle(self, *args, **options):
        if not Storage.objects.exists():
            Storage(base_path=settings.STORAGE_DIR, primary=True).save()
        else:
            storage = Storage.objects.get(primary=True)
            if storage.base_path != settings.STORAGE_DIR:
                storage.base_path = settings.STORAGE_DIR
                storage.save()
        if not User.objects.exists():
            User.objects.create_superuser(username=settings.ADMIN_USER,
                                          email=settings.ADMIN_USER+'@rpidrive.com',
                                          password=settings.ADMIN_PASSWORD)
        if getattr(settings, 'ARIA2_DISK_CACHE', None) is not None:
            update_disk_cache()