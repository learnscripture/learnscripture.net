from __future__ import absolute_import

from datetime import timedelta
from decimal import Decimal
import math

from django.db.models import F
from django.core.urlresolvers import reverse

from accounts.models import Identity, Account
from accounts.memorymodel import MM
from awards.models import AwardType, StudentAward, AceAward
from bibleverses.models import VerseSet, MemoryStage, StageType
from scores.models import Scores

from .base import FullBrowserTest


class LearnTests(FullBrowserTest):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json', 'test_verse_sets.json']

    kjv_john_3_16 = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life. John 3 16"

    psalm_23_1_2 = "The LORD is my shepherd I shall not want He maketh me to lie down in green pastures he leadeth me beside the still waters Psalm 23 1 2"

    def _get_current_identity(self):
        return Identity.objects.order_by('-date_created')[0]

    def choose_verse_set(self, name):
        verse_set = VerseSet.objects.get(name=name)
        self.get_url('choose')
        self.click("#id-learn-verseset-btn-%d" % verse_set.id)
        self.set_preferences()
        self.assertUrlsEqual(reverse('learn'))
        return verse_set

    def add_verse_set(self, name):
        verse_set = VerseSet.objects.get(name=name)
        self.get_url('preferences')  # ensure we have an Identity
        self.set_preferences()
        identity = self._get_current_identity()
        identity.add_verse_set(verse_set, identity.default_bible_version)
        return verse_set

    def _type_john_3_16_kjv(self, accuracy=1.0):
        accumulator = 0
        for word in self.kjv_john_3_16.strip().split():
            accumulator += accuracy
            if accumulator >= 1.0:
                self.fill({"#id-typing": word + " "})
                accumulator -= 1.0
            else:
                # Type the wrong thing - 3 times to make it fail
                for i in range(0, 3):
                    self.fill({"#id-typing": "xxx "})
        self.wait_for_ajax()

    def _score_for_j316(self, accuracy=1.0):
        word_count = len(self.kjv_john_3_16.strip().split())
        # This is the accuracy that will be recorded, given the
        # algo in _type_john_3_16_kjv and learn.js
        actual_accuracy = math.floor(word_count * accuracy) / word_count

        points_word_count = word_count - 3  # Don't get points for the reference
        return math.floor(Scores.POINTS_PER_WORD * points_word_count * actual_accuracy)

    def test_save_strength(self):
        verse_set = self.choose_verse_set('Bible 101')
        identity = self._get_current_identity()

        # Preconditions - should have been set up by choose_verse_set
        self.assertEqual(verse_set.verse_choices.count(), identity.verse_statuses.count())
        self.assertTrue(all(uvs.strength == Decimal('0.0') and
                            uvs.last_tested is None and
                            uvs.memory_stage == MemoryStage.ZERO
                            for uvs in identity.verse_statuses.all()))

        self.assertEqual(u"John 3:16", self.get_element_text("#id-verse-title"))
        # Do the reading:
        for i in range(0, 9):
            self.click("#id-next-btn")

        # Do the typing:
        self._type_john_3_16_kjv()

        self.wait_for_ajax()

        # Check the strength
        uvs = identity.verse_statuses.get(reference='John 3:16')
        self.assertEqual(uvs.strength, MM.INITIAL_STRENGTH_FACTOR)

    def test_typing_verse_combo(self):
        identity, account = self.create_account()
        self.login(account)

        identity.add_verse_choice('Psalm 23:1-2')
        self.get_url('dashboard')
        self.submit('input[name=learnbiblequeue]')
        self.assertEqual(u"Psalm 23:1-2", self.get_element_text("#id-verse-title"))

        # # Do the reading:
        # for i in range(0, 9):
        #     self.click("#id-next-btn")

        # self.wait_for_ajax()

        # # Do the typing: The fixture has 'The Lord is my shepherd--I shall not
        # # want' in order to test an issue with word splitting
        # for word in self.psalm_23_1_2.strip().split():
        #     self.fill({"#id-typing": word + " "})

        # self.wait_for_ajax()
        # # Check the strength
        # uvs = identity.verse_statuses.get(reference='Psalm 23:1-2')
        # self.assertEqual(uvs.strength, MM.INITIAL_STRENGTH_FACTOR)

        # # Check the score
        # points_for_verse = (
        #     (len(self.psalm_23_1_2.strip().split()) - 4)  # don't count reference
        #     * Scores.POINTS_PER_WORD)
        # self.assertEqual(Account.objects.get(id=account.id).total_score.points,
        #                  points_for_verse +
        #                  points_for_verse * Scores.PERFECT_BONUS_FACTOR +
        #                  StudentAward(count=1).points() +
        #                  AceAward(count=1).points()
        #                  )

    def test_points_and_student_award(self):
        identity, account = self.create_account()
        self.login(account)
        self.choose_verse_set('Bible 101')

        # Do the reading:
        for i in range(0, 9):
            self.click("#id-next-btn")

        # Do the typing:
        self._type_john_3_16_kjv()

        # Check scores

        j316_score = self._score_for_j316()
        self.assertEqual(Account.objects.get(id=account.id).total_score.points,
                         j316_score +
                         (j316_score * Scores.PERFECT_BONUS_FACTOR) +
                         StudentAward(count=1).points() +
                         AceAward(count=1).points()
                         )
        self.assertEqual(account.action_logs.count(), 4)

        # Check awards
        self.assertEqual(account.awards.filter(award_type=AwardType.STUDENT,
                                               level=1).count(), 1)

        # Go back to dashboard, and should see message
        self.get_url('dashboard')
        self.assertTextPresent("You've earned a new badge")

    def test_change_version_passage(self):
        self.choose_verse_set('Psalm 23')

        self.assertEqual(u"Psalm 23:1", self.get_element_text("#id-verse-title"))
        self.assertIn(u"I shall not want", self.get_element_text('.current-verse'))

        self.fill_by_text({"#id-version-select": "NET"})

        self.wait_for_ajax()
        self.assertIn(u"I lack nothing",
                      self.get_element_text('.current-verse'))

        # This section can be replaced by a 'skip' button click once we've implemented that.
        for i in range(0, 9):
            self.click("#id-next-btn")
        for word in "The LORD is my shepherd, I lack nothing.".split():
            self.fill({"#id-typing": word + " "})
        self.click("#id-next-verse-btn")

        # Now check that the next verse is present and is also NET, which is the
        # main point of this test.
        self.assertIn(u"He takes me to lush pastures",
                      self.get_element_text('.current-verse'))

    def test_revise_passage_mixed(self):
        # Test revising a passage when some verses are to be tested and others
        # are just being read.
        identity, account = self.create_account()
        self.login(account)

        self.add_verse_set('Psalm 23')

        for i in range(1, 7):
            identity.record_verse_action('Psalm 23:%d' % i, 'KJV', StageType.TEST,
                                         1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(reference='Psalm 23:1'))

        self.get_url('dashboard')
        self.submit('input[name=revisepassage]')

        for word in "The LORD is my shepherd, I shall not want.".split():
            self.fill({"#id-typing": word + " "})

        # Test keyboard shortcut
        self.send_keys('body', '\n')
        self.assertIn(u"He maketh me to lie down in green pastures",
                      self.get_element_text('.current-verse'))

        for i in range(0, 5):
            self.click("#id-context-next-verse-btn")
        self.assertUrlsEqual(reverse('dashboard'))

    def test_skip_verse(self):
        self.choose_verse_set('Bible 101')

        self.assertEqual(u"John 3:16", self.get_element_text("#id-verse-title"))

        self.click("#id-verse-dropdown")
        self.click("#id-skip-verse-btn")

        self.assertEqual(u"John 14:6", self.get_element_text("#id-verse-title"))

        # Should be removed from session too
        self.get_url('learn')

        self.assertEqual(u"John 14:6", self.get_element_text("#id-verse-title"))

    def test_cancel_learning(self):
        self.add_verse_set('Bible 101')

        identity = self._get_current_identity()
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        identity.record_verse_action('John 14:6', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses)

        # Go to dashboard
        self.get_url('dashboard')
        self.choose_revise_bible()

        self.assertEqual(u"John 3:16", self.get_element_text("#id-verse-title"))

        self.click("#id-verse-dropdown")
        self.click("#id-cancel-learning-btn")

        # Should skip.
        self.assertEqual(u"John 14:6", self.get_element_text("#id-verse-title"))

        # If we go back to dashboard and choose again, it should not appear
        # Go to dashboard
        self.get_url('dashboard')
        self.choose_revise_bible()

        self.assertEqual(u"John 14:6", self.get_element_text("#id-verse-title"))

    def test_reset_progress(self):
        self.add_verse_set('Bible 101')
        identity = self._get_current_identity()
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        self._make_verses_due_for_testing(identity.verse_statuses)

        self.get_url('dashboard')
        self.choose_revise_bible()

        self.assertEqual(u"John 3:16", self.get_element_text("#id-verse-title"))

        self.click("#id-verse-dropdown")
        self.click_and_confirm("#id-reset-progress-btn")

        # Should reset strength to zero
        self.assertEqual(identity.verse_statuses.get(reference='John 3:16').strength,
                         0)
        # Should revert to initial read mode
        self.assertTrue(self.is_element_displayed('#id-instructions .stage-read'))

    def choose_revise_bible(self):
        self.submit("input[name='revisebiblequeue']")

    def _make_verses_due_for_testing(self, uvs_queryset):
        uvs_queryset.update(
            last_tested=F('last_tested') - timedelta(100),
            next_test_due=F('next_test_due') - timedelta(100),
        )

    def test_finish_button(self):
        self.add_verse_set('Bible 101')

        identity = self._get_current_identity()
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        identity.record_verse_action('John 14:6', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses)

        self.get_url('dashboard')
        self.choose_revise_bible()

        self._type_john_3_16_kjv()

        self.click("#id-finish-btn")
        self.wait_for_ajax()

        # Reload, should have nothing more to revise

        self.get_url('learn')
        self.assertTrue(self.is_element_displayed("#id-no-verse-queue"))

    def test_more_practice(self):
        # tests that the 'more practice' button appears, and works

        identity, account = self.create_account()
        self.login(account)
        self.add_verse_set('Bible 101')

        # Learn one
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(memory_stage=MemoryStage.TESTED))

        self.get_url('dashboard')
        self.choose_revise_bible()

        self._type_john_3_16_kjv(accuracy=0.5)

        # Now the 'more practice' button will appear, and be primary
        self.assertIn('primary', self.get_element_attribute("#id-more-practice-btn", 'class').split())
        self.click("#id-more-practice-btn")

        # Now go through 3 stages:
        for i in range(0, 3):
            self.assertEqual(self.get_element_attribute("#id-next-btn", "disabled"),
                             None)
            self.click("#id-next-btn")

        self._type_john_3_16_kjv(accuracy=0.95)

        # We should get points for each time revised (and award)
        j316_score_1 = self._score_for_j316(accuracy=0.5)
        j316_score_2 = self._score_for_j316(accuracy=0.95)
        account = Account.objects.get(id=account.id)  # refresh
        self.assertEqual(account.total_score.points,
                         (j316_score_1 +
                          j316_score_2) +
                         StudentAward(count=1).points()
                         )
        self.assertEqual(account.action_logs.count(), 3)

    def test_hint_button(self):
        identity, account = self.create_account()
        self.login(account)
        self.add_verse_set('Bible 101')

        # Learn one
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(memory_stage=MemoryStage.TESTED))

        self.get_url('dashboard')
        self.choose_revise_bible()
        for i in range(0, 4):
            self.assertEqual(self.get_element_attribute("#id-hint-btn", "disabled"),
                             None)

            self.click("#id-hint-btn")

        # First two words should not be visually marked correct
        for i in range(0, 2):
            classes = self.get_element_attribute("#id-word-%d" % i, "class").split()
            self.assertNotIn('correct', classes)

        # Hint button should be disabled after 4 clicks
        self.assertEqual(self.get_element_attribute("#id-hint-btn", "disabled"),
                         'true')
