import logging
import sys

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            from datetime import timedelta

            from django.conf import settings
            from django.db.models import Count
            from django.utils import timezone

            from accounts.models import Identity

            # For now, we keep old Identity objects that have some
            # verse_statuses, because this might be useful for stats. Identity
            # objects with nothing associated are definitely not interesting.
            Identity.objects.filter(
                account__isnull=True, date_created__lt=timezone.now() - timedelta(days=settings.IDENTITY_EXPIRES_DAYS)
            ).annotate(verse_statuses_count=Count("verse_statuses")).filter(verse_statuses_count=0).delete()
        except Exception:
            logger.error("Couldn't clean old identities", exc_info=sys.exc_info())
