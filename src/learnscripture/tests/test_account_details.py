from django.utils import timezone

from accounts.models import Account

from .base import WebTestBase


class AccountDetailsTests(WebTestBase):
    def test_change_first_name(self):
        identity, account = self.create_account()
        self.login(account, shortcut=False)
        self.get_url("account_details")
        self.fill({"#id_first_name": "Fred"})
        self.submit("#id-save-btn")
        assert Account.objects.get(id=account.id).first_name == "Fred"

    def test_reset_email_bounced(self):
        identity, account = self.create_account()
        account.email_bounced = timezone.now()
        account.save()
        self.login(account)
        self.get_url("account_details")
        self.fill({"#id_first_name": "Fred"})
        self.submit("#id-save-btn")
        assert Account.objects.get(id=account.id).first_name == "Fred"
        assert Account.objects.get(id=account.id).email_bounced is not None

        self.fill({"#id_email": "a_different_email@gmail.com"})
        self.submit("#id-save-btn")

        assert Account.objects.get(id=account.id).email == "a_different_email@gmail.com"
        assert Account.objects.get(id=account.id).email_bounced is None
