from .base import WebTestBase


class AccountDetailsTests(WebTestBase):

    def test_change_language(self):
        identity, account = self.create_account(is_tester=True)
        self.login(account)
        self.get_url('dashboard')
        self.fill({'#id-language-chooser-form select': 'tr'})
        self.submit('#id-language-chooser-form [type="submit"]')
        identity.refresh_from_db()
        self.assertEqual(identity.interface_language, 'tr')
