from __future__ import absolute_import
import time, re

from django.core.urlresolvers import reverse
from django.test import TestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

from awards.models import AwardType
from bibleverses.models import VerseSet, VerseSetType, VerseChoice, StageType
from events.models import Event, EventType

from .base import LiveServerTests


class CreateSetTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(CreateSetTests, self).setUp()
        self._identity, self._account = self.create_account()

    def _add_ref(self, ref):
        driver = self.driver
        driver.find_element_by_id("id_quick_find").clear()
        driver.find_element_by_id("id_quick_find").send_keys(ref)
        driver.find_element_by_id("id_lookup").click()
        self.wait_for_ajax()
        driver.find_element_by_css_selector("input.add-to-set").click()
        self.wait_until_loaded('#id-verse-list tbody tr td')
        time.sleep(0.1)

    def test_create_selection_set(self):
        self.login(self._account)
        driver = self.driver
        self.get_url('create_selection_set')
        driver.find_element_by_id("id_name").clear()
        driver.find_element_by_id("id_name").send_keys("My set")
        driver.find_element_by_id("id_description").clear()
        driver.find_element_by_id("id_description").send_keys("My description")
        self._add_ref("Gen 1:5")
        self.assertIn("And God called the light Day", driver.page_source)

        driver.find_element_by_id("id_public").click()
        driver.find_element_by_id("id-save-btn").click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.title.startswith("Verse set: My set"))
        self.assertIn("And God called the light Day", driver.page_source)

        self.assertEqual(self._account.awards.filter(award_type=AwardType.SHARER).count(),
                         1)
        self.assertEqual(Event.objects.filter(event_type=EventType.VERSE_SET_CREATED).count(),
                         1)

    def test_dedupe_selection_sets(self):
        self.login(self._account)
        driver = self.driver
        self.get_url("create_selection_set")
        driver.find_element_by_id("id_name").send_keys("My set")

        # Add Gen 1:5
        self._add_ref("Genesis 1:5")

        driver.find_element_by_id("id-save-btn").click()
        self.wait_until_loaded('body')

        vs = VerseSet.objects.get(name='My set')
        self.assertEqual(len(vs.verse_choices.all()), 1)

        current_ref_list = [("Genesis 1:5", 0)]

        def _add_new_ref(ref):
            # Edit again
            self.get_url('edit_set', kwargs=dict(slug=vs.slug))
            self._add_ref(ref)

            driver.find_element_by_id("id-save-btn").click()
            self.wait_until_loaded('body')

            self.assertIn("Verse set 'My set' saved", driver.page_source) # Checks we didn't get 500

            if ref not in [r for r, i in current_ref_list]:
                current_ref_list.append((ref, len(current_ref_list)))

            self.assertEqual(current_ref_list,
                             sorted([(vc.reference, vc.set_order)
                                     for vc in vs.verse_choices.all()]))

        # Caching could cause these to fail
        _add_new_ref("Genesis 1:6")
        _add_new_ref("Genesis 1:6")
        _add_new_ref("Genesis 1:7")
        _add_new_ref("Genesis 1:7")


    def test_forget_name(self):
        """
        If they forget the name, it should not validate,
        but shouldn't forget the verse list
        """
        self.login(self._account)
        driver = self.driver
        self.get_url('create_selection_set')

        self._add_ref("Gen 1:5")
        self._add_ref("Gen 1:6")

        driver.find_element_by_id("id-save-btn").click()

        self.wait_until_loaded('body')
        self.assertTrue(driver.title.startswith("Create selection set"))
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
        self.get_url('edit_set', kwargs=dict(slug=vs.slug))
        e = driver.find_element_by_css_selector("#id-verse-list tbody tr:first-child td")
        ActionChains(driver).drag_and_drop_by_offset(e, 0, 110).perform()

        driver.find_element_by_id("id-save-btn").click()

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
        self.get_url('edit_set', kwargs=dict(slug=vs.slug))
        driver.find_element_by_css_selector("#id-verse-list tbody tr:first-child td .icon-trash").click()
        driver.find_element_by_id("id-save-btn").click()

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all()
        self.assertEqual(sorted(vc.id for vc in vcs), sorted([vc2.id]))

        # Need to ensure that the UVS has not been deleted
        uvs = identity.verse_statuses.get(version__slug='KJV', reference='Genesis 1:1')

    def test_require_account(self):
        driver = self.driver
        self.get_url('create_selection_set')
        self.set_preferences()
        self.assertIn('You need to', driver.page_source)
        self.assertIn('create an account', driver.page_source)

    def test_create_passage_set(self):
        self.login(self._account)
        driver = self.driver
        self.get_url('create_passage_set')

        driver.find_element_by_id("id_name").clear()
        driver.find_element_by_id("id_name").send_keys("Genesis 1:1-10")
        driver.find_element_by_id("id_description").clear()
        driver.find_element_by_id("id_description").send_keys("My description")

        driver.find_element_by_id("id_quick_find").clear()
        driver.find_element_by_id("id_quick_find").send_keys("Gen 1:1-10")
        driver.find_element_by_id("id_lookup").click()
        self.wait_for_ajax()
        self.wait_until_loaded('#id-verse-list tbody tr td')
        self.assertIn("And God called the light Day", driver.page_source)

        # Check boxes for Genesis 1:3, 1:9
        driver.find_element_by_css_selector('#id-verse-list tbody tr:nth-child(3) input').click()
        driver.find_element_by_css_selector('#id-verse-list tbody tr:nth-child(9) input').click()

        driver.find_element_by_id("id-save-btn").click()
        self.wait_until_loaded('body')
        self.assertTrue(driver.title.startswith("Verse set: Genesis 1"))
        self.assertIn("And God called the light Day", driver.page_source)

        vs = VerseSet.objects.get(name='Genesis 1:1-10',
                                  set_type=VerseSetType.PASSAGE)
        self.assertTrue(len(vs.verse_choices.all()), 10)
        self.assertEqual(vs.breaks, "1:3,1:9")
        self.assertEqual(vs.passage_id, 'Genesis 1:1 - Genesis 1:10')

    def test_create_duplicate_passage_set(self):
        self.test_create_passage_set()
        driver = self.driver

        self.get_url("create_passage_set")
        driver.find_element_by_id("id_quick_find").clear()
        driver.find_element_by_id("id_quick_find").send_keys("Gen 1:1-10")

        driver.find_element_by_id("id_lookup").click()
        self.wait_for_ajax()
        self.wait_until_loaded('#id-verse-list tbody tr td')
        self.assertIn("There are already", driver.page_source)

    def test_empty_passage_set(self):
        self.login(self._account)
        driver = self.driver
        self.get_url("create_passage_set")
        self.wait_until_loaded('body')
        driver.find_element_by_id("id_name").send_keys("xxx")
        driver.find_element_by_id("id-save-btn").click()
        self.wait_until_loaded('body')
        self.assertIn("No verses in set", driver.page_source)

    def test_edit_passage_set(self):
        self.login(self._account)
        driver = self.driver
        vs = VerseSet.objects.create(created_by=self._account,
                                     set_type=VerseSetType.PASSAGE,
                                     name='Psalm 23',
                                     breaks="23:5")
        references = []
        for i in range(1, 7):
            ref = 'Psalm 23:%d' % i
            references.append(ref)
            vs.verse_choices.create(reference=ref,
                                    set_order=i - 1)

        # Simple test - editing and pressing save should leave
        # everything the same.
        self.get_url('edit_set', kwargs=dict(slug=vs.slug))
        driver.find_element_by_id("id-save-btn").click()

        vs = VerseSet.objects.get(id=vs.id)
        vcs = vs.verse_choices.all().order_by('set_order')
        self.assertEqual([vc.reference for vc in vcs],
                         references)
        self.assertEqual(vs.breaks, "23:5")
