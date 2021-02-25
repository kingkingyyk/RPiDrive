from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from ...models import StorageProvider, LocalFileObject
from ...utils.indexer import LocalStorageProviderIndexer
from threading import Thread
from django.core.cache import cache
import logging
import time
import traceback

logging.basicConfig(level=logging.INFO)

class Command(BaseCommand):
    help = 'Run Job Server'

    @staticmethod
    def do_sync(period: int):
        while True:
            logging.info('Started indexing...')
            for fo in LocalFileObject.objects.select_related('storage_provider').filter(parent=None).all():
                try:
                    LocalStorageProviderIndexer.sync(fo)
                    cache.delete('storage-provider-{}'.format(fo.storage_provider.pk))
                    logging.info('Done indexing...')
                except KeyboardInterrupt:
                    return
                except SystemExit:
                    return
                except:
                    logging.error('Failed indexing - %s', str(traceback.format_exc()))
            time.sleep(period)

    def handle(self, *args, **options):
        indexer_period_seconds = settings.INDEXER_PERIOD*60
        Thread(target=Command.do_sync, args=(indexer_period_seconds,)).start()
        logging.info('Started periodic indexing every {} minutes.'.format(settings.INDEXER_PERIOD))