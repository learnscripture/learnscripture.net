from django.core.management.base import BaseCommand

from accounts.models import notify_all_accounts


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("language_code")
        parser.add_argument("message_html")

    def handle(self, language_code, message_html, **options):
        notify_all_accounts(language_code, message_html)
