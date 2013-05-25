from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
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
        driver = self.driver
        driver.find_element_by_link_text('Create an account').click()
        self.wait_until_loaded('body')
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
        self.wait_for_ajax()



def sqla_tear_down():
    from learnscripture.utils import sqla
    sqla.default_engine.pool.dispose()


class LiveServerTests(AccountTestMixin, LiveServerTestCase):

    hide_browser = True

    @classmethod
    def setUpClass(cls):
        from pyvirtualdisplay import Display
        if cls.hide_browser:
            cls.display = Display(visible=0, size=(1024, 768))
            cls.display.start()
        cls.driver = webdriver.Chrome() # Using Chrome because we have problem with drag and drop for Firefox
        cls.driver.implicitly_wait(1)
        super(LiveServerTests, cls).setUpClass()


    @classmethod
    def tearDownClass(cls):
        super(LiveServerTests, cls).tearDownClass()
        cls.driver.quit()
        if cls.hide_browser:
            cls.display.stop()

    def setUp(self):
        super(LiveServerTests, self).setUp()
        self.verificationErrors = []

    def tearDown(self):
        self.assertEqual([], self.verificationErrors)
        super(LiveServerTests, self).tearDown()
        sqla_tear_down()


    # Utilities:
    def get_url(self, name, *args, **kwargs):
        self.driver.get(self.live_server_url + reverse(name, *args, **kwargs))

    def find(self, css_selector):
        return self.driver.find_element_by_css_selector(css_selector)

    def click(self, css_selector):
        return self.find(css_selector).click()

    def send_keys(self, css_selector, text):
        return self.find(css_selector).send_keys(text)

    def wait_until(self, callback, timeout=10):
        """
        Helper function that blocks the execution of the tests until the
        specified callback returns a value that is not falsy. This function can
        be called, for example, after clicking a link or submitting a form.
        See the other public methods that call this function for more details.
        """
        WebDriverWait(self.driver, timeout).until(callback)

    def wait_for_ajax(self):
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
            self.wait_for_ajax()
        else:
            self.click("#id-save-btn")
            self.wait_until_loaded('body')

    def login(self, account):
        driver = self.driver
        self.get_url('dashboard')
        self.click("#id-session-menu")
        driver.find_element_by_link_text("Sign in").click()
        self.fill_in_login_form(account)
        self.wait_until_loaded('.logout-link')
        elem = self.find("#id-session-menu")
        self.assertEqual(elem.text, account.username)

    def fill_in_login_form(self, account):
        driver = self.driver
        self.wait_until_loaded('body')
        self.find("#id_login-email").clear()
        self.send_keys("#id_login-email", account.email)
        self.find("#id_login-password").clear()
        self.send_keys("#id_login-password", "password")
        self.click("input[name=signin]")

