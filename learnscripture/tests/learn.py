from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal
import math
import re
import time

from django.db.models import F
from django.core.urlresolvers import reverse
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from accounts.models import Identity, Account
from accounts.memorymodel import MM
from awards.models import AwardType, StudentAward, AceAward
from bibleverses.models import TextVersion, VerseSet, VerseSetType, VerseChoice, MemoryStage, StageType
from scores.models import Scores, ScoreReason

from .base import LiveServerTests


class LearnTests(LiveServerTests):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    kjv_john_3_16 = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life. John 3 16"

    psalm_23_1_2 = "The LORD is my shepherd I shall not want He maketh me to lie down in green pastures he leadeth me beside the still waters Psalm 23 1 2"

    def _get_current_identity(self):
        return Identity.objects.order_by('-date_created')[0]

    def choose_verse_set(self, name):
        verse_set = VerseSet.objects.get(name=name)
        driver = self.driver
        self.get_url('choose')
        driver.find_element_by_id("id-learn-verseset-btn-%d" % verse_set.id).click()
        self.set_preferences()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith('/learn/'))
        self.wait_for_ajax()
        return verse_set

    def add_verse_set(self, name):
        verse_set = VerseSet.objects.get(name=name)
        driver = self.driver
        self.get_url('preferences') # ensure we have an Identity
        self.set_preferences()
        identity = self._get_current_identity()
        identity.add_verse_set(verse_set, identity.default_bible_version)
        return verse_set

    def _type_john_3_16_kjv(self, accuracy=1.0):
        accumulator = 0
        for word in self.kjv_john_3_16.strip().split():
            accumulator += accuracy
            if accumulator >= 1.0:
                self.driver.find_element_by_id('id-typing').send_keys(word + ' ')
                accumulator -= 1.0
            else:
                # Type the wrong thing - 3 times to make it fail
                for i in range(0, 3):
                    self.driver.find_element_by_id('id-typing').send_keys(' ')

    def _score_for_j316(self, accuracy=1.0):
        word_count = len(self.kjv_john_3_16.strip().split())
        # This is the accuracy that will be recorded, given the
        # algo in _type_john_3_16_kjv and learn.js
        actual_accuracy = math.floor(word_count * accuracy)/word_count

        points_word_count = word_count - 3 # Don't get points for the reference
        return math.floor(Scores.POINTS_PER_WORD * points_word_count * actual_accuracy)

    def test_save_strength(self):
        verse_set = self.choose_verse_set('Bible 101')
        driver = self.driver
        identity = self._get_current_identity()

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
        uvs = identity.verse_statuses.get(reference='John 3:16')
        self.assertEqual(uvs.strength, MM.INITIAL_STRENGTH_FACTOR)

    def test_typing_verse_combo(self):
        identity, account = self.create_account()
        driver = self.driver
        self.login(account)

        identity.add_verse_choice('Psalm 23:1-2')
        self.get_url('dashboard')
        driver.find_element_by_css_selector('input[name=learnbiblequeue]').click()
        self.wait_for_ajax()
        self.assertEqual(u"Psalm 23:1-2", driver.find_element_by_id('id-verse-title').text)

        # Do the reading:
        for i in range(0, 9):
            driver.find_element_by_id('id-next-btn').click()

        # Do the typing: The fixture has 'The Lord is my shepherd--I shall not
        # want' in order to test an issue with word splitting
        for word in self.psalm_23_1_2.strip().split():
            self.driver.find_element_by_id('id-typing').send_keys(word + ' ')

        self.wait_for_ajax()

        # Check the strength
        uvs = identity.verse_statuses.get(reference='Psalm 23:1-2')
        self.assertEqual(uvs.strength, MM.INITIAL_STRENGTH_FACTOR)

        # Check the score
        points_for_verse = (
            (len(self.psalm_23_1_2.strip().split()) - 4) # don't count reference
            * Scores.POINTS_PER_WORD)
        self.assertEqual(account.total_score.points,
                         points_for_verse +
                         points_for_verse * Scores.PERFECT_BONUS_FACTOR +
                         StudentAward(count=1).points() +
                         AceAward(count=1).points()
                         )

    def test_points_and_student_award(self):
        identity, account = self.create_account()
        self.login(account)
        verse_set = self.choose_verse_set('Bible 101')
        self.wait_until_loaded('body')
        self.wait_for_ajax()
        driver = self.driver

        # Do the reading:
        for i in range(0, 9):
            driver.find_element_by_id('id-next-btn').click()

        # Do the typing:
        self._type_john_3_16_kjv()

        self.wait_for_ajax()

        # Check scores

        j316_score = self._score_for_j316()
        self.assertEqual(account.total_score.points,
                         j316_score +
                         (j316_score * Scores.PERFECT_BONUS_FACTOR) +
                         StudentAward(count=1).points() +
                         AceAward(count=1).points()
                         )
        self.assertEqual(account.score_logs.count(), 4)

        # Check awards
        self.assertEqual(account.awards.filter(award_type=AwardType.STUDENT,
                                               level=1).count(), 1)

        # Go back to dashboard, and should see message
        self.get_url('dashboard')
        self.assertIn("You've earned a new badge", driver.page_source)


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

    def test_revise_passage_mixed(self):
        # Test revising a passage when some verses are to be tested and others
        # are just being read.
        import time
        driver = self.driver
        identity, account = self.create_account()
        self.login(account)

        verse_set = self.add_verse_set('Psalm 23')

        for i in range(1, 7):
            identity.record_verse_action('Psalm 23:%d' % i, 'KJV', StageType.TEST,
                                         1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(reference='Psalm 23:1'))

        self.get_url('dashboard')
        driver.find_element_by_css_selector('input[name=revisepassage]').click()

        self.wait_until_loaded('body')
        self.wait_for_ajax()

        for word in "The LORD is my shepherd, I shall not want.".split():
            driver.find_element_by_id('id-typing').send_keys(word + ' ')

        # Test keyboard shortcut
        driver.find_element_by_css_selector('body').send_keys('\n')
        self.wait_for_ajax()
        self.assertIn(u"He maketh me to lie down in green pastures",
                      driver.find_element_by_css_selector('.current-verse').text)

        btn = driver.find_element_by_id('id-context-next-verse-btn')
        for i in range(0, 5):
            btn.click()

        self.wait_for_ajax()
        self.wait_until_loaded('body')
        self.assertTrue(driver.current_url.endswith('/dashboard/'))

    def test_skip_verse(self):
        verse_set = self.choose_verse_set('Bible 101')
        driver = self.driver

        self.assertEqual(u"John 3:16", driver.find_element_by_id('id-verse-title').text)

        driver.find_element_by_id('id-verse-dropdown').click()
        driver.find_element_by_id('id-skip-verse-btn').click()

        self.assertEqual(u"John 14:6", driver.find_element_by_id('id-verse-title').text)

        # Should be removed from session too
        self.get_url('learn')
        self.wait_for_ajax()

        self.assertEqual(u"John 14:6", driver.find_element_by_id('id-verse-title').text)

    def test_cancel_learning(self):
        verse_set = self.add_verse_set('Bible 101')
        driver = self.driver

        identity = self._get_current_identity()
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        identity.record_verse_action('John 14:6', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses)

        # Go to dashboard
        self.get_url('dashboard')
        self.click_revise_bible()

        self.assertEqual(u"John 3:16", driver.find_element_by_id('id-verse-title').text)

        driver.find_element_by_id('id-verse-dropdown').click()
        driver.find_element_by_id('id-cancel-learning-btn').click()
        self.wait_for_ajax()

        # Should skip.
        self.assertEqual(u"John 14:6", driver.find_element_by_id('id-verse-title').text)

        # If we go back to dashboard and choose again, it should not appear
        # Go to dashboard
        self.get_url('dashboard')
        self.click_revise_bible()

        self.assertEqual(u"John 14:6", driver.find_element_by_id('id-verse-title').text)

    def test_reset_progress(self):
        verse_set = self.add_verse_set('Bible 101')
        driver = self.driver
        identity = self._get_current_identity()
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        self._make_verses_due_for_testing(identity.verse_statuses)

        self.get_url('dashboard')
        self.click_revise_bible()

        self.assertEqual(u"John 3:16", driver.find_element_by_id('id-verse-title').text)

        driver.find_element_by_id('id-verse-dropdown').click()
        driver.find_element_by_id('id-reset-progress-btn').click()

        alert = driver.switch_to_alert()
        alert.accept()
        self.wait_until_loaded('body')
        self.wait_for_ajax()

        # Should reset strength to zero
        self.assertEqual(identity.verse_statuses.get(reference='John 3:16').strength,
                         0)
        # Should revert to initial read mode
        self.assertTrue(driver.find_element_by_css_selector('#id-instructions .stage-read').is_displayed())

    def click_revise_bible(self):
        self.driver.find_element_by_css_selector("input[name='revisebiblequeue']").click()
        self.wait_until_loaded('body')
        self.wait_for_ajax()

    def _make_verses_due_for_testing(self, uvs_queryset):
        uvs_queryset.update(
            last_tested=F('last_tested') - timedelta(100),
            next_test_due=F('next_test_due') - timedelta(100),
            )


    def test_finish_button(self):
        verse_set = self.add_verse_set('Bible 101')
        driver = self.driver

        identity = self._get_current_identity()
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        identity.record_verse_action('John 14:6', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses)

        self.get_url('dashboard')
        self.click_revise_bible()

        self._type_john_3_16_kjv()

        driver.find_element_by_id('id-finish-btn').click()
        self.wait_for_ajax()

        # Reload, should have nothing more to revise

        self.get_url('learn')

        self.wait_until_loaded('body')
        self.wait_for_ajax()

        self.assertTrue(driver.find_element_by_id('id-no-verse-queue').is_displayed())


    def test_more_practice(self):
        # tests that the 'more practice' button appears, and works

        driver = self.driver
        identity, account = self.create_account()
        self.login(account)
        verse_set = self.add_verse_set('Bible 101')

        # Learn one
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(memory_stage=MemoryStage.TESTED))

        self.get_url('dashboard')
        self.click_revise_bible()

        self._type_john_3_16_kjv(accuracy=0.5)

        self.wait_for_ajax()

        # Now the 'more practice' button will appear, and be primary
        btn = driver.find_element_by_id('id-more-practice-btn')
        self.assertTrue('primary' in btn.get_attribute('class'))

        btn.click()

        # Now go through 3 stages:
        for i in range(0, 3):
            next_btn = driver.find_element_by_id('id-next-btn')
            self.assertNotEqual(next_btn.get_attribute('disabled'), 'true')
            next_btn.click()

        self._type_john_3_16_kjv(accuracy=0.95)
        self.wait_for_ajax()

        # We should get points for each time revised (and award)
        j316_score_1 = self._score_for_j316(accuracy=0.5)
        j316_score_2 = self._score_for_j316(accuracy=0.95)
        account = Account.objects.get(id=account.id) # refresh
        self.assertEqual(account.total_score.points,
                         (j316_score_1
                          + j316_score_2)
                         + StudentAward(count=1).points()
                         )
        self.assertEqual(account.score_logs.count(), 3)

    def test_hint_button(self):
        driver = self.driver
        identity, account = self.create_account()
        self.login(account)
        verse_set = self.add_verse_set('Bible 101')

        # Learn one
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(memory_stage=MemoryStage.TESTED))

        self.get_url('dashboard')
        self.click_revise_bible()
        for i in range(0, 4):
            hint_btn = driver.find_element_by_id('id-hint-btn')
            self.assertEqual(hint_btn.get_attribute('disabled'),
                             None)
            hint_btn.click()

        # First two words should be marked correct
        for i in range(0, 2):
            self.assertIn('correct', driver.find_element_by_id('id-word-%d' % i).get_attribute('class'))

        # Hint button should be disabled after 4 clicks
        self.assertEqual(driver.find_element_by_id('id-hint-btn').get_attribute('disabled'),
                         'true')
