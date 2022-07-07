import logging
from django.core.management.base import BaseCommand
from drive.views.web.shared import reset_spam_protect

class Command(BaseCommand):
    """Command to reset spam protect list"""
    help = 'Reset spam protect list'

    def handle(self, *args, **options):
        reset_spam_protect()
        logging.info('Done')
