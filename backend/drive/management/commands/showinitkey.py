import uuid
from django.core.management.base import BaseCommand
from drive.models import System


class Command(BaseCommand):
    """Command to display initialization key"""
    help = 'Display the initialization key'

    def handle(self, *args, **options):
        system = System.objects.first()
        save_system = not system or not system.init_key
        if not system:
            system = System()
        if not system.init_key:
            system.init_key = str(uuid.uuid4())
        if save_system:
            system.save()
        print('Initialization Key : '+system.init_key)
