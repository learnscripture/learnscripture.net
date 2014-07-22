import sys

from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        from bibleverses.suggestions import generate_suggestions
        from bibleverses.models import TextVersion, BIBLE_BOOKS
        for v in TextVersion.objects.filter(slug__in=['KJV', 'NET', 'ESV']):
            for b in BIBLE_BOOKS:
                generate_suggestions(b, v, missing_only=True)
