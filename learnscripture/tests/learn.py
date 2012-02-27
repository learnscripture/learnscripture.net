from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal
import re

from django.core.urlresolvers import reverse
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from accounts.models import Identity
from accounts.memorymodel import m as memorymodel
from bibleverses.models import BibleVersion, VerseSet, VerseSetType, VerseChoice, MemoryStage, StageType
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

    def _type_john_3_16_kjv(self):

        text = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life. John 3:16"
        for word in text.strip().split():
            self.driver.find_element_by_id('id-typing').send_keys(word + ' ')


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
        # Do the reading:
        for i in range(0, 9):
            driver.find_element_by_id('id-next-btn').click()

        # Do the typing:
        self._type_john_3_16_kjv()

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
        for word in "The LORD is my shepherd, I lack nothing.".split():
            driver.find_element_by_id('id-typing').send_keys(word + ' ')
        driver.find_element_by_id('id-next-verse-btn').click()

        # Now check that the next verse is present and is also NET, which is the
        # main point of this test.
        self.wait_for_ajax()
        self.assertIn(u"He takes me to lush pastures",
                      driver.find_element_by_css_selector('.current-verse').text)

    def test_learn_passage_mixed(self):
        import time
        # Test learning a passage when some verses are to be tested and others
        # are just being read.
        verse_set = self.choose_verse_set('Psalm 23')

        driver = self.driver
        identity = Identity.objects.get() # should only be one at this point

        for i in range(1, 7):
            identity.record_verse_action('Psalm 23:%d' % i, 'KJV', StageType.TEST,
                                         1.0)
        # Make some due for testing:
        identity.verse_statuses.filter(verse_choice__reference='Psalm 23:1')\
            .update(last_tested=timezone.now() - timedelta(100))

        driver.get(self.live_server_url + reverse('learn'))
        for word in "The LORD is my shepherd, I shall not want.".split():
            driver.find_element_by_id('id-typing').send_keys(word + ' ')

        # Test keyboard shortcut
        driver.find_element_by_id('id-typing').send_keys('\n')
        self.wait_for_ajax()
        self.assertIn(u"He maketh me to lie down in green pastures",
                      driver.find_element_by_css_selector('.current-verse').text)

    def test_skip_verse(self):
        verse_set = self.choose_verse_set('Bible 101')
        driver = self.driver

        self.assertEqual(u"John 3:16", driver.find_element_by_id('id-verse-title').text)

        driver.find_element_by_id('id-skip-verse-btn').click()

        self.assertEqual(u"John 14:6", driver.find_element_by_id('id-verse-title').text)

        # Should be removed from session too
        driver.get(self.live_server_url + reverse('learn'))
        self.wait_for_ajax()

        self.assertEqual(u"John 14:6", driver.find_element_by_id('id-verse-title').text)

    def test_cancel_learning(self):
        verse_set = self.choose_verse_set('Bible 101') 
        driver = self.driver

        identity = Identity.objects.get() # should only be one at this point
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        identity.record_verse_action('John 14:6', 'KJV', StageType.TEST, 1.0)

        # Make it due for testing:
        identity.verse_statuses.update(last_tested=timezone.now() - timedelta(100))

        # Go to dashboard
        driver.get(self.live_server_url + reverse('start'))
        # and click 'Revise'
        driver.find_element_by_css_selector("input[name='revisequeue']").click()

        self.wait_until_loaded('body')
        self.wait_for_ajax()

        self.assertEqual(u"John 3:16", driver.find_element_by_id('id-verse-title').text)

        driver.find_element_by_id('id-cancel-learning-btn').click()
        self.wait_for_ajax()

        # Should skip.
        self.assertEqual(u"John 14:6", driver.find_element_by_id('id-verse-title').text)

        # If we go back to dashboard and choose again, it should not appear
        # Go to dashboard
        driver.get(self.live_server_url + reverse('start'))
        # and click 'Revise'
        driver.find_element_by_css_selector("input[name='revisequeue']").click()

        self.wait_until_loaded('body')
        self.wait_for_ajax()

        self.assertEqual(u"John 14:6", driver.find_element_by_id('id-verse-title').text)

    def test_finish_button(self):
        verse_set = self.choose_verse_set('Bible 101')
        driver = self.driver

        identity = Identity.objects.get() # should only be one at this point
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        identity.record_verse_action('John 14:6', 'KJV', StageType.TEST, 1.0)

        # Make them due for testing:
        identity.verse_statuses.update(last_tested=timezone.now() - timedelta(100))

        # Go to dashboard
        driver.get(self.live_server_url + reverse('start'))
        # and click 'Revise'
        driver.find_element_by_css_selector("input[name='revisequeue']").click()

        self.wait_until_loaded('body')
        self.wait_for_ajax()

        self._type_john_3_16_kjv()

        driver.find_element_by_id('id-finish-btn').click()

        # Reload, should have nothing more to revise

        driver.get(self.live_server_url + reverse('learn'))

        self.wait_until_loaded('body')
        self.wait_for_ajax()

        self.assertTrue(driver.find_element_by_id('id-no-verse-queue').is_displayed())
