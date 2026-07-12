import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Load main entry points to check for import errors
        import learnscripture.urls  # noqa
        import learnscripture.views  # noqa

        print("Smoke test successful")
