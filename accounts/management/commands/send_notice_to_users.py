from django.core.management.base import BaseCommand

from accounts.models import notify_all_accounts


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("message_html")

    def handle(self, message_html, **options):
        notify_all_accounts(message_html)
