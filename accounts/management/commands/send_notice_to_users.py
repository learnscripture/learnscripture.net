from django.core.management.base import BaseCommand
from accounts.models import notify_all_accounts

class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(args) != 1:
            raise Exception("Must provide message to send as sole argument")

        notify_all_accounts(args[0])
