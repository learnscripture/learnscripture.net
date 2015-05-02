from __future__ import absolute_import

from django.core.urlresolvers import reverse

from accounts.models import Account
from .base import FullBrowserTest


class AccountDetailsTests(FullBrowserTest):

    fixtures = ['test_bible_versions.json']

    def test_change_first_name(self):
        identity, account = self.create_account()
        self.login(account)
        self.driver.get(self.live_server_url)
        self.wait_until_loaded('body')

        self.click("#id-session-menu")
        # Should have an 'account' link

        self.click('ul.dropdown-menu li a[href="/account/"]')

        self.send_keys("#id_first_name", "Fred")
        self.click("#id-save-btn")

        self.assertEqual(Account.objects.get(id=account.id).first_name, "Fred")

    def test_redirect_if_not_logged_in(self):
        identity, account = self.create_account()
        self.get_url('account_details')
        self.fill_in_login_form(account)
        self.assertTrue(self.current_url.endswith(reverse('account_details')))


# TODO - test for changing email address - should reset email_bounced
