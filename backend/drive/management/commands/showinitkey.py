from django.core.management.base import BaseCommand, CommandError
from ...models import System
import uuid

class Command(BaseCommand):
    help = 'Display the initialization key'

    def handle(self, *args, **options):
        system = System.objects.first()
        if system.init_key is None:
            system.init_key = str(uuid.uuid4())
            system.save()
        print('Initialization Key : '+system.init_key)