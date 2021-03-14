from django.core.management.base import BaseCommand

from accounts.models import Account


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, username, **options):
        account = Account.objects.get(username=username)
        account.erase()
        self.stdout.write(f'User {username} erased to {account.username}\n')
