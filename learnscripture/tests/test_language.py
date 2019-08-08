# -*- coding: utf-8 -*-
from django_functest import FuncBaseMixin

from .base import AccountTestMixin, FullBrowserTest, WebTestBase


class LanguageTestsBase(AccountTestMixin, FuncBaseMixin):

    def test_change_language(self):
        identity, account = self.create_account(is_tester=True)
        self.login(account)
        self.get_url('dashboard')
        self.fill({'#id-language-chooser-form select': 'tr'})
        self.submit('#id-language-chooser-form [type="submit"]')
        identity.refresh_from_db()
        self.assertEqual(identity.interface_language, 'tr')

    def test_change_language_not_logged_in(self):
        self.get_url('choose')
        self.fill({'#id-language-chooser-form select': 'tr'})
        self.submit('#id-language-chooser-form [type="submit"]')
        self.assertTextPresent("Ayet seçme")


class LanguageTestsWT(LanguageTestsBase, WebTestBase):
    pass


class LanguageTestsFB(LanguageTestsBase, FullBrowserTest):
    def test_change_language_redirect(self):
        self.get_url('choose')
        self.click("#id-choose-verseset .accordion-heading")
        # This change the URL via PJAX without a page submit:
        self.click('#id_set_type_2')
        url = self.current_url
        self.fill({'#id-language-chooser-form select': 'tr'})
        self.submit('#id-language-chooser-form [type="submit"]')
        self.assertTextPresent("Ayet seçme")
        self.assertUrlsEqual(self.current_url, url)
