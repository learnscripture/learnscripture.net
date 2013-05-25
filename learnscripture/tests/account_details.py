from __future__ import absolute_import

from django.core.urlresolvers import reverse

from accounts.models import Account
from .base import LiveServerTests


class AccountDetailsTests(LiveServerTests):

    fixtures = ['test_bible_versions.json']

    def test_change_first_name(self):
        identity, account = self.create_account()
        self.login(account)
        driver = self.driver
        driver.get(self.live_server_url)

        self.find("#id-session-menu").click()
        # Should have an 'account' link

        self.find('ul.dropdown-menu li a[href="/account/"]').click()

        self.find("#id_first_name").send_keys("Fred")
        self.find("#id-save-btn").click()

        self.assertEqual(Account.objects.get(id=account.id).first_name, "Fred")

    def test_redirect_if_not_logged_in(self):
        identity, account = self.create_account()
        driver = self.driver
        self.get_url('account_details')
        self.fill_in_login_form(account)
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith(reverse('account_details')))
