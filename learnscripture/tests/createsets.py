from __future__ import absolute_import
import time, re

from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from accounts.models import Identity, Account
from bibleverses.models import BibleVersion, VerseSet, VerseSetType


class CreateSetTests(LiveServerTestCase):

    fixtures = ['test_bible_verses.json']

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Chrome() # Using Chrome because we have problem with drag and drop for Firefox
        cls.driver.implicitly_wait(30)
        super(CreateSetTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(CreateSetTests, cls).tearDownClass()
        cls.driver.quit()

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

    def setUp(self):
        KJV = BibleVersion.objects.get(slug='KJV')
        self._identity = Identity.objects.create(default_bible_version=KJV)
        self.verificationErrors = []
        self._account = Account.objects.create(email="test1@test.com",
                                               username="test1",
                                               )
        self._account.set_password('password')
        self._account.save()
        self._identity.account = self._account
        self._identity.save()

    def tearDown(self):
        self.assertEqual([], self.verificationErrors)


    def login(self):
        driver = self.driver
        driver.get(self.live_server_url + "/start/")
        driver.find_element_by_id("id-session-menu").click()
        driver.find_element_by_link_text("Sign in").click()
        driver.find_element_by_id("id_login-email").clear()
        driver.find_element_by_id("id_login-email").send_keys("test1@test.com")
        driver.find_element_by_id("id_login-password").clear()
        driver.find_element_by_id("id_login-password").send_keys("password")
        driver.find_element_by_id("id-sign-in-btn").click()
        self.wait_until_loaded('.logout-link')
        elem = driver.find_element_by_id('id-session-menu')
        self.assertEqual(elem.text, 'test1')

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True

    def test_create_set(self):
        self.login()
        driver = self.driver
        driver.get(self.live_server_url + "/create-verse-set/")
        driver.find_element_by_id("id_selection-name").clear()
        driver.find_element_by_id("id_selection-name").send_keys("My set")
        driver.find_element_by_id("id_selection-description").clear()
        driver.find_element_by_id("id_selection-description").send_keys("My description")
        Select(driver.find_element_by_id("id_selection-book")).select_by_visible_text("Genesis")
        driver.find_element_by_id("id_selection-chapter").clear()
        driver.find_element_by_id("id_selection-chapter").send_keys("1")
        driver.find_element_by_id("id_selection-start_verse").clear()
        driver.find_element_by_id("id_selection-start_verse").send_keys("5")
        driver.find_element_by_id("id-add-verse-btn").click()
        self.wait_until_loaded('#id-verse-list tbody tr td')
        self.assertIn("And God called the light Day", driver.page_source)

        driver.find_element_by_id("id-selection-save-btn").click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.title.startswith("Verse set: My set"))
        self.assertIn("And God called the light Day", driver.page_source)


    def test_forget_name(self):
        """
        If they forget the name, it should not validate,
        but shouldn't forget the verse list
        """
        self.login()
        driver = self.driver
        driver.get(self.live_server_url + "/create-verse-set/")
        Select(driver.find_element_by_id("id_selection-book")).select_by_visible_text("Genesis")
        driver.find_element_by_id("id_selection-chapter").clear()
        driver.find_element_by_id("id_selection-chapter").send_keys("1")
        driver.find_element_by_id("id_selection-start_verse").clear()
        driver.find_element_by_id("id_selection-start_verse").send_keys("5")
        driver.find_element_by_id("id-add-verse-btn").click()
        driver.find_element_by_id("id_selection-start_verse").clear()
        driver.find_element_by_id("id_selection-start_verse").send_keys("6")
        driver.find_element_by_id("id-add-verse-btn").click()

        driver.find_element_by_id("id-selection-save-btn").click()

        self.wait_until_loaded('body')
        self.assertTrue(driver.title.startswith("Create verse set"))
        self.assertIn("This field is required", driver.page_source)
        self.assertIn("Genesis 1:5", driver.page_source)
        self.assertIn("Genesis 1:6", driver.page_source)

    def test_edit(self):
        vs = VerseSet.objects.create(created_by=self._account,
                                     set_type=VerseSetType.SELECTION,
                                     name='my set')
        vc1 = vs.verse_choices.create(reference='Genesis 1:1',
                                      set_order=0)
        vc2 = vs.verse_choices.create(reference='Genesis 1:5',
                                      set_order=1)
        vc3 = vs.verse_choices.create(reference='Genesis 1:10',
                                      set_order=2)
        self.login()
        driver = self.driver
        driver.get(self.live_server_url + reverse('edit_set', kwargs=dict(slug=vs.slug)))
        e = driver.find_element_by_css_selector("#id-verse-list tbody tr:first-child td")
        ActionChains(driver).drag_and_drop_by_offset(e, 0, 100).perform()

        driver.find_element_by_id("id-selection-save-btn").click()

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual(sorted(vc.id for vc in vcs), sorted([vc1.id, vc2.id, vc3.id]))
        self.assertEqual(vs.verse_choices.get(reference='Genesis 1:1').set_order, 1)
        self.assertEqual(vs.verse_choices.get(reference='Genesis 1:5').set_order, 0)

