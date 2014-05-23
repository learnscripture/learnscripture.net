import sys

from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            from accounts.email_reminders import send_email_reminders
            send_email_reminders()
        except Exception:
            logger.error("Couldn't send email reminders", exc_info=sys.exc_info())
