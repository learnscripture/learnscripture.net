from __future__ import absolute_import

from decimal import Decimal
import re

from django.core.urlresolvers import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from accounts.models import Identity
from accounts.memorymodel import m as memorymodel
from bibleverses.models import BibleVersion, VerseSet, VerseSetType, VerseChoice, MemoryStage
from .base import LiveServerTests


class LearnTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    def choose_verse_set(self, name):
        verse_set = VerseSet.objects.get(name=name)
        driver = self.driver
        driver.get(self.live_server_url + reverse('choose'))
        driver.find_element_by_id("id-learn-verseset-btn-%d" % verse_set.id).click()
        self.set_preferences()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith('/learn/'))
        self.wait_for_ajax()
        return verse_set

    def test_save_strength(self):
        verse_set = self.choose_verse_set('Bible 101')
        driver = self.driver

        identity = Identity.objects.get() # should only be one at this point
        # Preconditions - should have been set up by choose_verse_set
        self.assertEqual(verse_set.verse_choices.count(), identity.verse_statuses.count())
        self.assertTrue(all(uvs.strength == Decimal('0.0') and
                            uvs.last_tested == None and
                            uvs.memory_stage == MemoryStage.ZERO
                            for uvs in identity.verse_statuses.all()))

        self.assertEqual(u"John 3:16", driver.find_element_by_id('id-verse-title').text)

        text = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life. John 3:16"

        # Do the reading:
        for i in range(0, 9):
            driver.find_element_by_id('id-next-btn').click()

        # Do the typing:
        for word in text.strip().split():
            driver.find_element_by_id('id-typing').send_keys(word + ' ')

        self.wait_for_ajax()

        # Check the strength
        uvs = identity.verse_statuses.get(verse_choice__reference='John 3:16')
        self.assertEqual(uvs.strength, memorymodel.INITIAL_STRENGTH_FACTOR)

    def test_choose_individual_verse(self):
        driver = self.driver
        driver.get(self.live_server_url + reverse('choose'))
        driver.find_element_by_css_selector("a[href='#id-tab-individual']").click()
        Select(driver.find_element_by_id("id_book")).select_by_visible_text("John")
        driver.find_element_by_id("id_chapter").send_keys("3")
        driver.find_element_by_id("id_start_verse").send_keys("16")
        driver.find_element_by_css_selector("input[name=lookup]").click()
        self.wait_until_loaded('body')

        self.assertIn("For this is the way God loved the world", driver.page_source)

        driver.find_element_by_css_selector("#id-tab-individual input[value=Learn]").click()
        self.set_preferences()
        self.wait_until_loaded('body')
        self.wait_for_ajax()
        self.assertEqual(driver.find_element_by_id("id-verse-title").text, u"John 3:16")

    def test_change_version_passage(self):
        verse_set = self.choose_verse_set('Psalm 23')
        driver = self.driver

        self.assertEqual(u"Psalm 23:1", driver.find_element_by_id('id-verse-title').text)
        self.assertIn(u"I shall not want", driver.find_element_by_css_selector('.current-verse').text)

        Select(driver.find_element_by_id("id-version-select")).select_by_visible_text("NET")

        self.wait_for_ajax()
        self.assertIn(u"I lack nothing",
                      driver.find_element_by_css_selector('.current-verse').text)

        # This section can be replaced by a 'skip' button click once we've implemented that.
        for i in range(0, 9):
            driver.find_element_by_id('id-next-btn').click()
        for word in "A psalm of David. The LORD is my shepherd, I lack nothing. Psalm 23:1".split():
            driver.find_element_by_id('id-typing').send_keys(word + ' ')
        driver.find_element_by_id('id-next-verse-btn').click()

        # Now check that the next verse is present and is also NET, which is the
        # main point of this test.
        self.wait_for_ajax()
        self.assertIn(u"He takes me to lush pastures",
                      driver.find_element_by_css_selector('.current-verse').text)
