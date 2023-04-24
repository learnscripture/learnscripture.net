from django.core.management.base import BaseCommand

from moderation.models import run_moderation_adjustments


class Command(BaseCommand):
    def handle(self, *args, **options):
        run_moderation_adjustments()
