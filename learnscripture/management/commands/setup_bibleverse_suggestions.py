
from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        from bibleverses.suggestions import generate_suggestions
        from bibleverses.models import TextVersion
        for v in TextVersion.objects.all():
            generate_suggestions(v, missing_only=True)
