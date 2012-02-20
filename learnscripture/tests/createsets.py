from __future__ import absolute_import
import time, re

from django.core.urlresolvers import reverse
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

from accounts.models import Identity, Account, TestingMethod
from bibleverses.models import BibleVersion, VerseSet, VerseSetType, VerseChoice

from .base import LiveServerTests


class CreateSetTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(CreateSetTests, self).setUp()
        KJV = BibleVersion.objects.get(slug='KJV')
        self._identity = Identity.objects.create(default_bible_version=KJV,
                                                 testing_method=TestingMethod.FULL_WORDS)
        self._account = Account.objects.create(email="test1@test.com",
                                               username="test1",
                                               )
        self._account.set_password('password')
        self._account.save()
        self._identity.account = self._account
        self._identity.save()

    def login(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('start'))
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
        self.wait_until_loaded('#id-selection-verse-list tbody tr td')
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
        driver.get(self.live_server_url + reverse('create_set'))
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
        e = driver.find_element_by_css_selector("#id-selection-verse-list tbody tr:first-child td")
        ActionChains(driver).drag_and_drop_by_offset(e, 0, 110).perform()

        driver.find_element_by_id("id-selection-save-btn").click()

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual(sorted(vc.id for vc in vcs), sorted([vc1.id, vc2.id, vc3.id]))
        self.assertEqual(vs.verse_choices.get(reference='Genesis 1:1').set_order, 1)
        self.assertEqual(vs.verse_choices.get(reference='Genesis 1:5').set_order, 0)


    def test_remove(self):
        self.login()
        vs = VerseSet.objects.create(created_by=self._account,
                                     set_type=VerseSetType.SELECTION,
                                     name='my set')
        vc1 = vs.verse_choices.create(reference='Genesis 1:1',
                                      set_order=0)
        vc2 = vs.verse_choices.create(reference='Genesis 1:5',
                                      set_order=1)
        driver = self.driver
        driver.get(self.live_server_url + reverse('edit_set', kwargs=dict(slug=vs.slug)))
        driver.find_element_by_css_selector("#id-selection-verse-list tbody tr:first-child td a").click()
        driver.find_element_by_id("id-selection-save-btn").click()

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual(sorted(vc.id for vc in vcs), sorted([vc2.id]))

        # Need to ensure that the removed item has been orphaned, not deleted.
        vc1_new = VerseChoice.objects.get(id=vc1.id)
        self.assertEqual(vc1_new.verse_set_id, None)

    def test_require_account(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('create_set'))
        self.set_preferences()
        self.assertIn('You need to', driver.page_source)
        self.assertIn('create an account', driver.page_source)

    def test_create_passage_set(self):
        self.login()
        driver = self.driver
        driver.get(self.live_server_url + "/create-verse-set/")
        driver.find_element(By.CSS_SELECTOR, "a[href='#id-tab-passage']").click()
        driver.find_element_by_id("id_passage-name").clear()
        driver.find_element_by_id("id_passage-name").send_keys("Genesis 1")
        driver.find_element_by_id("id_passage-description").clear()
        driver.find_element_by_id("id_passage-description").send_keys("My description")
        Select(driver.find_element_by_id("id_passage-book")).select_by_visible_text("Genesis")
        driver.find_element_by_id("id_passage-start_chapter").clear()
        driver.find_element_by_id("id_passage-start_chapter").send_keys("1")
        driver.find_element_by_id("id_passage-start_verse").clear()
        driver.find_element_by_id("id_passage-start_verse").send_keys("1")
        driver.find_element_by_id("id_passage-end_verse").clear()
        driver.find_element_by_id("id_passage-end_verse").send_keys("10")
        driver.find_element_by_id("id-lookup-passage-btn").click()
        self.wait_until_loaded('#id-passage-verse-list tbody tr td')
        self.assertIn("And God called the light Day", driver.page_source)

        driver.find_element_by_id("id-passage-save-btn").click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.title.startswith("Verse set: Genesis 1"))
        self.assertIn("And God called the light Day", driver.page_source)

        vs = VerseSet.objects.get(name='Genesis 1',
                                  set_type=VerseSetType.PASSAGE)
        self.assertTrue(len(vs.verse_choices.all()), 10)
