import logging
import os
import time
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from names_generator import generate_name
from rpidrive.controllers.local_file import (
    perform_index,
    process_compress_job,
)
from rpidrive.models import (
    Job,
    JobKind,
    PublicFileLink,
    Volume,
    VolumeKindEnum,
)


class Command(BaseCommand):
    """Start job server command"""

    help = "Start job server"
    logger = logging.getLogger(__name__)

    def handle(self, *args, **options):
        """Handle command"""
        # Create init key if needed
        has_superuser = User.objects.filter(is_superuser=True).exists()
        if not has_superuser:
            if not os.path.exists(settings.INIT_KEY_PATH):
                username = generate_name()
                password = str(uuid.uuid4())
                User.objects.create_superuser(
                    username, f"{username}@example.com", password
                )
                with open(settings.INIT_KEY_PATH, "w+") as f_h:
                    f_h.write("Superuser account :\n")
                    f_h.write(f"  Username: {username}\n")
                    f_h.write(f"  Password: {password}\n")

            with open(settings.INIT_KEY_PATH, "r") as f_h:
                self.logger.info(f_h.read())

        # Run jobs
        last_indexed_lim = timezone.now() - timedelta(
            minutes=settings.ROOT_CONFIG.indexer.period
        )
        while True:
            self.logger.info("HELLOOO")
            for volume in Volume.objects.all():
                print(volume.last_indexed)

            volumes = Volume.objects.filter(
                Q(kind=VolumeKindEnum.HOST_PATH)
                & (
                    Q(indexing=True)
                    | Q(last_indexed=None)
                    | Q(last_indexed__lte=last_indexed_lim)
                )
            ).all()
            for volume in volumes:
                self.logger.info("Performing indexing on volume %s", volume.name)
                perform_index(volume)
                self.logger.info("Done indexing volume %s", volume.name)

            zip_jobs = Job.objects.filter(kind=JobKind.ZIP).all()
            for job in zip_jobs:
                self.logger.info("Performing job #%s", job.pk)
                process_compress_job(job)
                job.delete()

            PublicFileLink.objects.filter(
                expire_time__lte=timezone.now()
            ).all().delete()

            time.sleep(15.0)
