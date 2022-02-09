import logging
from operator import index
import time
import traceback
from django.conf import settings
from django.core.management.base import BaseCommand
from drive.models import LocalFileObject
from drive.utils.indexer import LocalStorageProviderIndexer

logging.basicConfig(level=logging.INFO)

class Command(BaseCommand):
    """Command to start jobserver"""
    help = 'Run Job Server'

    @staticmethod
    def do_sync(period: int):
        """Perform file-index synchronization periodically"""
        while True:
            logging.info('Started indexing...')
            for f_o in LocalFileObject.objects.select_related(
                'storage_provider').filter(parent=None).all():
                try:
                    LocalStorageProviderIndexer.sync(f_o)
                    logging.info('Done indexing...')
                except KeyboardInterrupt:
                    return
                except SystemExit:
                    return
                except: # pylint: disable=bare-except
                    logging.error('Failed indexing - %s', str(traceback.format_exc()))
            time.sleep(period)

    def handle(self, *args, **options):
        indexer_period_seconds = settings.INDEXER_PERIOD*60
        logging.info('Started periodic indexing every %s minutes.', settings.INDEXER_PERIOD)
        Command.do_sync(indexer_period_seconds)
