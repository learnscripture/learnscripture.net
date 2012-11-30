import os
import sys

from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            import learnscripture.metrics
            learnscripture.metrics.record_active_accounts()
        except Exception as e:
            logger.error("Couldn't create metrics", exc_info=sys.exc_info())
