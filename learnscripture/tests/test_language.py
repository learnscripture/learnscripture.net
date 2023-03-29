from pathlib import Path

import toml
from django.conf import settings
from django_functest import FuncBaseMixin

from .base import AccountTestMixin, BibleVersesMixin, FullBrowserTest, WebTestBase


class LanguageTestsBase(AccountTestMixin, FuncBaseMixin):
    def test_change_language(self):
        identity, account = self.create_account(is_tester=True)
        self.login(account)
        self.get_url("dashboard")
        self.fill({"#id-language-chooser-form select": "tr"})
        self.submit('#id-language-chooser-form [type="submit"]')
        identity.refresh_from_db()
        assert identity.interface_language == "tr"

    def test_change_language_not_logged_in(self):
        self.get_url("choose")
        self.fill({"#id-language-chooser-form select": "tr"})
        self.submit('#id-language-chooser-form [type="submit"]')
        self.assertTextPresent("Ayet seçme")


class LanguageTestsWT(LanguageTestsBase, WebTestBase):
    pass


class LanguageTestsFB(LanguageTestsBase, BibleVersesMixin, FullBrowserTest):
    def test_change_language_redirect(self):
        self.get_url("choose")
        self.click("#id-choose-verseset .accordion-heading")
        # This change the URL via HTMX without a page submit:
        self.click("#id_set_type_2")
        url = self.current_url
        self.fill({"#id-language-chooser-form select": "tr"})
        self.submit('#id-language-chooser-form [type="submit"]')
        self.assertTextPresent("Ayet seçme")
        self.assertUrlsEqual(self.current_url, url)

    def test_setting_preferences_remembers_default_language(self):
        self.get_url("home")
        self.click('a[data-set-lang="tr"]')
        self.click('.maincontent a[href="/choose/"]')
        self.click("#id-choose-individual > button")
        self.fill({"#id_quick_find": "Mezmurlar 23:1"})
        self.click("#id_lookup")
        self.click('[name="learn_now"]')
        self.set_preferences(bible_version="TCL02 (Kutsal Kitap Yeni Çeviri)")
        self.wait_until_loaded(".help-tour-welcome")
        self.assertTextPresent("Selam! Bu gezinti size çalışma sayfası arabirimini tanıtır.")


def test_l10n_toml_updated():
    l10n_toml = toml.load(Path(settings.SRC_ROOT) / "l10n.toml")
    for code, _ in settings.LANGUAGES:
        assert code in l10n_toml["locales"]
        if code != "en":
            assert code in l10n_toml["paths"][0]["locales"]
