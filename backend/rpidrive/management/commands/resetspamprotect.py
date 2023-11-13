import logging

from django.core.management.base import BaseCommand
from django.core.cache import cache
from rpidrive.views.decorators.mixins import BruteForceProtectMixin


class Command(BaseCommand):
    """Start job server command"""

    help = "Reset spam protect"
    logger = logging.getLogger(__name__)

    def handle(self, *args, **options):
        """Handle command"""
        cache.delete_pattern(BruteForceProtectMixin.construct_key("*"))
        self.logger.info("Done.")
