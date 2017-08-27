import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger("bibleverses.suggestions")


class Command(BaseCommand):
    def handle(self, *args, **options):
        from bibleverses.suggestions.analyze import analyze_all
        analyze_all()
