from __future__ import absolute_import
import time, re

from django.core.urlresolvers import reverse
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

from bibleverses.models import VerseSet, VerseSetType, VerseChoice, StageType

from .base import LiveServerTests


class CreateSetTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(CreateSetTests, self).setUp()
        self._identity, self._account = self.create_account()

    def test_create_set(self):
        self.login(self._account)
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
        self.login(self._account)
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
        self.login(self._account)
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
        self.login(self._account)
        vs = VerseSet.objects.create(created_by=self._account,
                                     set_type=VerseSetType.SELECTION,
                                     name='my set')
        vc1 = vs.verse_choices.create(reference='Genesis 1:1',
                                      set_order=0)
        vc2 = vs.verse_choices.create(reference='Genesis 1:5',
                                      set_order=1)

        identity = self._identity
        # Record some learning against the verse we will remove
        identity.add_verse_set(vs)
        identity.record_verse_action('Genesis 1:1', 'KJV', StageType.TEST, 1.0)

        driver = self.driver
        driver.get(self.live_server_url + reverse('edit_set', kwargs=dict(slug=vs.slug)))
        driver.find_element_by_css_selector("#id-selection-verse-list tbody tr:first-child td a").click()
        driver.find_element_by_id("id-selection-save-btn").click()

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual(sorted(vc.id for vc in vcs), sorted([vc2.id]))

        # Need to ensure that the UVS has not been deleted
        uvs = identity.verse_statuses.get(version__slug='KJV', reference='Genesis 1:1')

    def test_require_account(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('create_set'))
        self.set_preferences()
        self.assertIn('You need to', driver.page_source)
        self.assertIn('create an account', driver.page_source)

    def test_create_passage_set(self):
        self.login(self._account)
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

        # Check boxes for Genesis 1:3, 1:9
        driver.find_element_by_css_selector('#id-passage-verse-list tbody tr:nth-child(3) input').click()
        driver.find_element_by_css_selector('#id-passage-verse-list tbody tr:nth-child(9) input').click()

        driver.find_element_by_id("id-passage-save-btn").click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.title.startswith("Verse set: Genesis 1"))
        self.assertIn("And God called the light Day", driver.page_source)

        vs = VerseSet.objects.get(name='Genesis 1',
                                  set_type=VerseSetType.PASSAGE)
        self.assertTrue(len(vs.verse_choices.all()), 10)
        self.assertEqual(vs.breaks, "1:3,1:9")

