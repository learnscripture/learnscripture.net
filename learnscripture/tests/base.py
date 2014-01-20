from __future__ import absolute_import
import time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from django.utils.importlib import import_module
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from accounts.models import Identity, Account, TestingMethod
from bibleverses.models import TextVersion


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



class AccountTestMixin(object):

    fixtures = ['test_bible_versions.json']

    def create_identity(self, version_slug='KJV', account=None):
        version = TextVersion.objects.get(slug=version_slug)
        return Identity.objects.create(default_bible_version=version,
                                       testing_method=TestingMethod.FULL_WORDS,
                                       enable_animations=False,
                                       enable_sounds=False,
                                       account=account,
                                       )

    def create_account(self,
                       version_slug='KJV',
                       email="test1@test.com",
                       username="test1"):
        account = Account.objects.create(email=email,
                                         username=username,
                                         )
        account.set_password('password')
        account.save()
        identity = self.create_identity(version_slug=version_slug, account=account)
        return (identity, account)

    def create_account_interactive(self,
                                   email="test2@test.com",
                                   username="test2",
                                   password="testpassword2"):
        self.click(self.driver.find_element_by_link_text('Create an account'))
        self.fill_in_account_form(email=email, username=username, password=password)

    def fill_in_account_form(self,
                             email="test2@test.com",
                             username="test2",
                             password="testpassword2"):
        driver = self.driver
        self.send_keys("#id_signup-email", email)
        self.send_keys("#id_signup-username", username)
        self.send_keys("#id_signup-password", password)
        self.click('input[name=signup]')


def sqla_tear_down():
    from learnscripture.utils import sqla
    sqla.default_engine.pool.dispose()


# https://code.google.com/p/selenium/source/browse/java/client/src/org/openqa/selenium/internal/ElementScrollBehavior.java
class ElementScrollBehavior(object):
    TOP = 0
    BOTTOM = 1


class LiveServerTests(AccountTestMixin, LiveServerTestCase):

    hide_browser = True

    @classmethod
    def setUpClass(cls):
        from pyvirtualdisplay import Display
        if cls.hide_browser:
            cls.display = Display(visible=0, size=(1024, 768))
            cls.display.start()
        capabilities = webdriver.DesiredCapabilities.FIREFOX.copy()
        # We have problems clicking on elements that are scrolled to the top in
        # order to click on them, but are then covered by the navbar at the
        # top. The fix is to use elementScrollBehavior
        # https://code.google.com/p/selenium/issues/detail?id=4297#c3
        capabilities['elementScrollBehavior'] = ElementScrollBehavior.BOTTOM
        cls.driver = webdriver.Firefox(capabilities=capabilities)
        cls.driver.implicitly_wait(1)
        super(LiveServerTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        if cls.hide_browser:
            cls.display.stop()
        super(LiveServerTests, cls).tearDownClass()

    def setUp(self):
        super(LiveServerTests, self).setUp()
        self.driver.delete_all_cookies()
        self.verificationErrors = []

    def tearDown(self):
        self.assertEqual([], self.verificationErrors)
        super(LiveServerTests, self).tearDown()
        sqla_tear_down()


    # Utilities:
    def setup_session(self):
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore()
        session.save()
        self.driver.get(self.live_server_url)
        self.driver.add_cookie({'domain': 'localhost',
                                'name': 'sessionid',
                                'value':session.session_key})
        return session

    def get_url(self, name, *args, **kwargs):
        self.driver.get(self.live_server_url + reverse(name, *args, **kwargs))
        self.wait_until_loaded('body')
        self.wait_for_ajax()

    def find(self, css_selector):
        return self.driver.find_element_by_css_selector(css_selector)

    def click(self, clickable, produces_alert=False):
        if hasattr(clickable, 'click'):
            retval = clickable.click()
        else:
            retval = self.find(clickable).click()
        if not produces_alert:
            # This will cause a Selenium error if an alert is open, and there
            # doesn't sem to be any way of detecting this case.
            self.wait_until_loaded('body')
            self.wait_for_ajax()
        return retval

    def send_keys(self, css_selector, text):
        retval = self.find(css_selector).send_keys(text)
        self.wait_for_ajax()
        return retval

    def confirm(self):
        self.driver.switch_to_alert().accept()
        self.wait_until_loaded('body')
        self.wait_for_ajax()

    def wait_until(self, callback, timeout=10):
        """
        Helper function that blocks the execution of the tests until the
        specified callback returns a value that is not falsy. This function can
        be called, for example, after clicking a link or submitting a form.
        See the other public methods that call this function for more details.
        """
        WebDriverWait(self.driver, timeout).until(callback)

    def wait_for_ajax(self):
        time.sleep(0.1)
        WebDriverWait(self.driver, 10).until(lambda driver: driver.execute_script('return jQuery.active == 0'))

    def wait_until_loaded(self, selector, timeout=10):
        """
        Helper function that blocks until the element with the given tag name
        is found on the page.
        """
        self.wait_until(
            lambda driver: driver.find_element(By.CSS_SELECTOR, selector),
            timeout
        )

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True

    def set_preferences(self):
        # Set preferences if visible
        driver = self.driver

        if not self.find("#id_testing_method_0").is_displayed():
            return

        Select(self.find("#id_default_bible_version")).select_by_visible_text("KJV (King James Version)")
        self.click("#id_testing_method_0")

        # Turn animations off, as they can complicate testing.
        e = self.find("#id_enable_animations")
        if e.get_attribute('checked'):
            e.click()

        if 'id-preferences-save-btn' in driver.page_source:
            # popup
            self.click("#id-preferences-save-btn")
        else:
            self.click("#id-save-btn")
        self.wait_until_loaded('body')
        self.wait_for_ajax()

    def login(self, account):
        driver = self.driver
        from django.contrib.sessions.backends.db import SessionStore
        from django.conf import settings
        s = SessionStore()
        s.create()
        s['identity_id'] = account.identity.id
        s.save()
        driver.get(self.live_server_url) # needed to be able to set cookie
        driver.add_cookie({'name':settings.SESSION_COOKIE_NAME,
                           'value': s.session_key})

    def fill_in_login_form(self, account):
        driver = self.driver
        self.wait_until_loaded('body')
        self.find("#id_login-email").clear()
        self.send_keys("#id_login-email", account.email)
        self.find("#id_login-password").clear()
        self.send_keys("#id_login-password", "password")
        self.click("input[name=signin]")

