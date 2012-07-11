from __future__ import absolute_import

from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase, TransactionTestCase
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from accounts.models import Identity, Account, TestingMethod
from bibleverses.models import BibleVersion


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

    def create_account(self):
        KJV = BibleVersion.objects.get(slug='KJV')
        identity = Identity.objects.create(default_bible_version=KJV,
                                           testing_method=TestingMethod.FULL_WORDS,
                                           enable_animations=False)
        account = Account.objects.create(email="test1@test.com",
                                          username="test1",
                                         )
        account.set_password('password')
        account.save()
        identity.account = account
        identity.save()
        return (identity, account)

    def create_account_interactive(self,
                                   email="test2@test.com",
                                   username="test2",
                                   password="testpassword2"):
        driver = self.driver
        driver.find_element_by_link_text('Create an account').click()
        self.wait_for_ajax()
        self.fill_in_account_form(email=email, username=username, password=password)

    def fill_in_account_form(self,
                             email="test2@test.com",
                             username="test2",
                             password="testpassword2"):
        driver = self.driver
        driver.find_element_by_id('id_signup-email').send_keys(email)
        driver.find_element_by_id('id_signup-username').send_keys(username)
        driver.find_element_by_id('id_signup-password').send_keys(password)
        driver.find_element_by_id('id-create-account-btn').click()
        self.wait_for_ajax()


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
        self.verificationErrors = []

    def tearDown(self):
        self.assertEqual([], self.verificationErrors)


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

        if not driver.find_element_by_id("id_testing_method_0").is_displayed():
            return

        Select(driver.find_element_by_id("id_default_bible_version")).select_by_visible_text("KJV (King James Version)")
        driver.find_element_by_id("id_testing_method_0").click()

        # Turn animations off, as they can complicate testing.
        e = driver.find_element_by_id('id_enable_animations')
        if e.get_attribute('checked'):
            e.click()

        if 'id-preferences-save-btn' in driver.page_source:
            # popup
            driver.find_element_by_id("id-preferences-save-btn").click()
            self.wait_for_ajax()
        else:
            driver.find_element_by_id("id-save-btn").click()
            self.wait_until_loaded('body')

    def login(self, account):
        driver = self.driver
        driver.get(self.live_server_url + reverse('dashboard'))
        driver.find_element_by_id("id-session-menu").click()
        driver.find_element_by_link_text("Sign in").click()
        self.fill_in_login_form(account)
        self.wait_until_loaded('.logout-link')
        elem = driver.find_element_by_id('id-session-menu')
        self.assertEqual(elem.text, account.username)

    def fill_in_login_form(self, account):
        driver = self.driver
        driver.find_element_by_id("id_login-email").clear()
        driver.find_element_by_id("id_login-email").send_keys(account.email)
        driver.find_element_by_id("id_login-password").clear()
        driver.find_element_by_id("id_login-password").send_keys("password")
        driver.find_element_by_id("id-sign-in-btn").click()


class UsesSQLAlchemyBase(TransactionTestCase):

    def tearDown(self):
        super(UsesSQLAlchemyBase, self).tearDown()
        from learnscripture.utils import sqla
        sqla.default_engine.pool.dispose()

