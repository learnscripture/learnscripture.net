from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = "<message html>"
    def handle(self, *args, **options):
        from accounts.models import Account

        message_html = args[0]
        for a in Account.objects.active():
            # Dedupe
            if not a.identity.notices.filter(message_html=message_html).exists():
                a.identity.notices.create(message_html=message_html)
