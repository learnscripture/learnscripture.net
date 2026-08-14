import logging
import sys

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            import awards.tasks

            awards.tasks.give_all_addict_awards()
            awards.tasks.give_all_consistent_learner_awards()
        except Exception:
            logger.error("Couldn't create awards", exc_info=sys.exc_info())
