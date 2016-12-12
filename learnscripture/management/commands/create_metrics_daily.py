import logging
import sys

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            import learnscripture.metrics
            learnscripture.metrics.record_active_accounts()
        except Exception:
            logger.error("Couldn't create metrics", exc_info=sys.exc_info())
