import os
import sys

from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            from awards.tasks import give_champion_awards
            give_champion_awards.delay()
        except Exception as e:
            logger.error("Couldn't create awards", exc_info=sys.exc_info())
