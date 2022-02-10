import logging
import time
import traceback
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
from drive.models import LocalFileObject
from drive.utils.indexer import LocalStorageProviderIndexer

class Command(BaseCommand):
    """Command to start jobserver"""
    help = 'Run Job Server'

    @staticmethod
    def sync_all(period: int):
        """Perform all file indexing on all storage providers"""
        for f_o in LocalFileObject.objects.select_related(
                'storage_provider').filter(parent=None).all():
            s_p = f_o.storage_provider
            flag = s_p.indexing or \
                not s_p.last_indexed or \
                s_p.last_indexed + timedelta(period) <= timezone.now()
            if not flag:
                break
            logging.info(f'Started indexing {s_p.name}...')
            try:
                LocalStorageProviderIndexer.sync(f_o)
                cache.delete(f'storage-provider-{f_o.storage_provider.pk}')
                logging.info('Done indexing...')
            except KeyboardInterrupt:
                return
            except SystemExit:
                return
            except: # pylint: disable=bare-except
                logging.error('Failed indexing - %s', str(traceback.format_exc()))

    def handle(self, *args, **options):
        indexer_period_seconds = settings.INDEXER_PERIOD*60
        logging.info('Started periodic indexing every %s minutes.', settings.INDEXER_PERIOD)
        while True:
            Command.sync_all(indexer_period_seconds)
            time.sleep(5.0)
