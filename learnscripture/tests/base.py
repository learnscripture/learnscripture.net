# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import time
import unittest

from compressor.filters import CompilerFilter
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django_functest import FuncSeleniumMixin, FuncWebTestMixin
from selenium.webdriver.common.action_chains import ActionChains

from accounts.models import Account, Identity
from bibleverses.models import TextVersion

TESTS_SHOW_BROWSER = os.environ.get('TESTS_SHOW_BROWSER', '')


class FuzzyInt(int):
    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)


# We don't need less compilation when running normal tests, and it adds a lot to
# the test run (nearly 1 sec per view, due to shelling out). We leave it on for
# FullBrowserTest, because CSS could easily effect whether elements are
# clickable etc.
class DummyLessCssFilter(CompilerFilter):
    def __init__(self, content, command=None, *args, **kwargs):
        pass

    def input(self, **kwargs):
        return ''


class AccountTestMixin(object):

    fixtures = ['test_bible_versions.json']

    def create_identity(self, version_slug='KJV', account=None):
        version = TextVersion.objects.get(slug=version_slug)
        return Identity.objects.create(default_bible_version=version,
                                       enable_animations=False,
                                       enable_sounds=False,
                                       account=account,
                                       )

    def create_account(self,
                       version_slug='KJV',
                       email="test1@test.com",
                       username="tëst1"):
        account = Account.objects.create(email=email,
                                         username=username,
                                         last_login=timezone.now(),
                                         )
        account.set_password('password')
        account.save()
        identity = self.create_identity(version_slug=version_slug, account=account)
        return (identity, account)

    def create_account_interactive(self,
                                   email="test2@test.com",
                                   username="tëst2",
                                   password="testpassword2"):
        self.click(text='Create an account')
        self.fill_in_account_form(email=email, username=username, password=password)

    def fill_in_account_form(self,
                             email="test2@test.com",
                             username="tëst2",
                             password="testpassword2"):
        self.fill({"#id_signup-email": email,
                   "#id_signup-username": username,
                   "#id_signup-password": password})
        self.submit('input[name=signup]')


def sqla_tear_down():
    from learnscripture.utils import sqla
    sqla.default_engine.pool.dispose()


class SqlaCleanup(object):

    def tearDown(self):
        sqla_tear_down()
        super(SqlaCleanup, self).tearDown()


class LoginMixin(object):

    def fill_in_login_form(self, account):
        self.fill({"#id_login-email": account.email,
                   "#id_login-password": "password"})
        self.submit("input[name=signin]")

    def login(self, account, shortcut=True):
        if shortcut:
            self.setup_identity(identity=account.identity)
        else:
            self.get_url('login')
            self.fill_in_login_form(account)

    def setup_identity(self, identity=None):
        if identity is None:
            Identity.objects.all().delete()
            identity = Identity.objects.create()
            identity.default_bible_version = TextVersion.objects.get(slug='NET')
            identity.save()

        self.set_session_data({'identity_id': identity.id})
        return identity


@unittest.skipIf(os.environ.get('SKIP_SELENIUM_TESTS'), "Skipping Selenium tests")
class FullBrowserTest(AccountTestMixin, LoginMixin, FuncSeleniumMixin, SqlaCleanup, StaticLiveServerTestCase):

    display = TESTS_SHOW_BROWSER
    default_timeout = 20
    page_load_timeout = 40

    # Overridden:

    def click(self, *args, **kwargs):
        super(FullBrowserTest, self).click(*args, **kwargs)
        self.wait_for_ajax()

    def submit(self, *args, **kwargs):
        super(FullBrowserTest, self).submit(*args, **kwargs)
        self.wait_for_ajax()

    def get_literal_url(self, *args, **kwargs):
        super(FullBrowserTest, self).get_literal_url(*args, **kwargs)
        self.wait_for_ajax()

    # Utilities:

    # We use some django-functest internals here, rather than in actual test
    # classes, to minimize impact if django-functest changes

    # WebTest/Selenium utilities

    def click_and_confirm(self, selector):
        # 'self.click' is buggy when alerts are produced.
        # So we wrap all of this functionality in a utility
        # to avoid issues.
        self._find(selector).click()
        self._driver.switch_to_alert().accept()
        self.wait_for_page_load()
        self.wait_for_ajax()

    def get_element_text(self, css_selector):
        return self._find(css_selector).text

    def get_element_attribute(self, css_selector, attribute_name):
        return self._find(css_selector).get_attribute(attribute_name)

    # Selenium specific utilities:

    def drag_and_drop_by_offset(self, css_selector, x_offset, y_offset):
        e = self._find(css_selector)
        ActionChains(self._driver).drag_and_drop_by_offset(e, x_offset, y_offset).perform()

    def get_page_title(self):
        return self._driver.title

    def send_keys(self, css_selector, keys):
        self._find(css_selector=css_selector).send_keys(keys)

    def wait_for_ajax(self):
        time.sleep(0.1)
        self.wait_until(lambda driver: driver.execute_script('return (typeof(jQuery) == "undefined" || jQuery.active == 0)'))

    # Higher level, learnscripture specific things:

    def set_preferences(self):
        # Set preferences if visible

        if not self._find("#id_desktop_testing_method_0").is_displayed():
            return

        self.fill_by_text({"#id_default_bible_version": "KJV (King James Version)"})

        # Turn animations off, as they can complicate testing.
        self.fill({"#id_enable_animations": False})

        if 'id-preferences-save-btn' in self._driver.page_source:
            # popup
            self.click("#id-preferences-save-btn")
        else:
            self.submit("#id-save-btn")
        self.wait_until_loaded('body')
        self.wait_for_ajax()


@override_settings(COMPRESS_PRECOMPILERS=[('text/less', 'learnscripture.tests.base.DummyLessCssFilter')],
                   )
class WebTestBase(AccountTestMixin, LoginMixin, FuncWebTestMixin, TestCase):

    # Utilities:

    # WebTest/Selenium utilities

    # Use some django-functest internals here

    def click_and_confirm(self, css_selector):
        # No javascript, just submit the button
        self.submit(css_selector)

    def get_element_text(self, css_selector):
        return self._make_pq(self.last_response).find(css_selector).text()

    def get_element_attribute(self, css_selector, attribute_name):
        return self._make_pq(self.last_response).find_(css_selector).attr(attribute_name)


@override_settings(COMPRESS_PRECOMPILERS=[('text/less', 'learnscripture.tests.base.DummyLessCssFilter')],
                   )
class TestBase(TestCase):
    pass
