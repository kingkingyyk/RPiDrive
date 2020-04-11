from django.core.management.base import BaseCommand, CommandError
from drive.models import Storage
from django.contrib.auth.models import User
from django.conf import settings

class Command(BaseCommand):
    help = 'Run first time initialization'

    def handle(self, *args, **options):
        if not Storage.objects.exists():
            Storage(base_path=settings.STORAGE_DIR).save()
        if not User.objects.exists():
            User.objects.create_superuser(username=settings.ADMIN_USER,
                                          email=settings.ADMIN_USER+'@rpidrive.com',
                                          password=settings.ADMIN_PASSWORD)