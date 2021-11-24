from django.core.management.base import BaseCommand

from bibleverses.services import adjust_stored_esv


class Command(BaseCommand):
    def handle(self, *args, **options):
        adjust_stored_esv("ESV")
