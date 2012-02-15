from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait


class LiveServerTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Chrome() # Using Chrome because we have problem with drag and drop for Firefox
        cls.driver.implicitly_wait(30)
        super(LiveServerTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(LiveServerTests, cls).tearDownClass()
        cls.driver.quit()

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
        # Set preferences
        driver = self.driver
        Select(driver.find_element_by_id("id_default_bible_version")).select_by_visible_text("KJV")
        driver.find_element_by_id("id_testing_method_0").click()
        driver.find_element_by_id("id-save-btn").click()
        self.wait_until_loaded('body')
