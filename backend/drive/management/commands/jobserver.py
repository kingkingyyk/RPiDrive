import json
import logging
import os
import shutil
import stat
import time
import traceback
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from drive.cache import ModelCache
from drive.core.local_file_object import zip_files
from drive.models import (
    FileObjectType,
    Job,
    LocalFileObject,
)
from drive.request_models import ZipFileRequest
from drive.utils.indexer import LocalStorageProviderIndexer

class Command(BaseCommand):
    """Command to start jobserver"""
    help = 'Run Job Server'

    @staticmethod
    def sync_once(root_folder: LocalFileObject, period: int):
        s_p = root_folder.storage_provider
        flag = not s_p.last_indexed
        if period:
            flag = flag or\
                s_p.last_indexed + timedelta(minutes=period) <= timezone.now()
        if not flag:
            return
        logging.info(f'Started indexing {s_p.name}...')
        try:
            LocalStorageProviderIndexer.sync(root_folder)
            ModelCache.clear(root_folder.storage_provider)
            logging.info('Done indexing...')
        except (KeyboardInterrupt, SystemExit) as exc:
            raise exc
        except: # pylint: disable=bare-except
            logging.error('Failed indexing - %s', str(traceback.format_exc()))

    @staticmethod
    def sync_all(period: int):
        """Perform all file indexing on all storage providers"""
        for root_folder in LocalFileObject.objects.select_related(
                'storage_provider').filter(parent=None).all():
            Command.sync_once(root_folder, period)

    @staticmethod
    def create_zip(job: Job):
        request = ZipFileRequest.parse_obj(json.loads(job.data))
        logging.info(job.description)
        try:
            destination_file = LocalFileObject.objects.get(pk=request.destination)

            for file, completion in zip_files(LocalFileObject.objects.filter(pk__in=request.files)):
                job.progress_info = f'Compressing {file}'
                job.progress_value = completion
                job.save(update_fields=['progress_info', 'progress_value'])
                temp_zip_path = file
            # Last file = output_zip_file
            path = os.path.join(destination_file.full_path, request.filename)

            job.progress_info = 'Moving...'
            job.save(update_fields=['progress_info'])
            if os.path.exists(path): # Delete existing file
                LocalFileObject.objects.filter(
                    name=request.filename,
                    parent=destination_file,
                ).all().delete()
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.chmod(path, stat.S_IWRITE)
                    os.remove()
            shutil.move(temp_zip_path, path)

            # Create file object
            LocalFileObject(
                name=request.filename,
                obj_type=FileObjectType.FILE,
                parent=destination_file,
                storage_provider=destination_file.storage_provider,
                rel_path=os.path.join(destination_file.rel_path, request.filename),
                last_modified=datetime.fromtimestamp(
                    os.path.getmtime(path), tz=timezone.get_current_timezone()),
                size=os.path.getsize(path),
            ).save()

            logging.info('Done')
        except (KeyboardInterrupt, SystemExit) as exc:
            raise exc
        except: # pylint: disable=bare-except
            logging.error('Failed zip file creation - %s', str(traceback.format_exc()))

    @staticmethod
    def process_jobs():
        jobs = Job.objects.all()
        for job in jobs:
            if job.task_type == Job.TaskTypes.INDEX:
                root_folder = (
                    LocalFileObject.objects
                    .select_related('storage_provider')
                    .filter(storage_provider__pk=job.data, parent=None)
                    .first()
                )
                if root_folder:
                    Command.sync_once(root_folder, 0)
            elif job.task_type == Job.TaskTypes.ZIP:
                Command.create_zip(job)
            job.delete()

    def handle(self, *args, **options):
        logging.info('Started periodic indexing every %s minutes.', settings.INDEXER_PERIOD)
        while True:
            Command.process_jobs()
            Command.sync_all(settings.INDEXER_PERIOD)
            time.sleep(5.0)
