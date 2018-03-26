import math
import time
from datetime import timedelta
from decimal import Decimal

from django.db.models import signals
from django.urls import reverse
from django.utils import timezone

from accounts.memorymodel import MM
from accounts.models import Account, Identity
from awards.models import AceAward, AwardType, StudentAward
from bibleverses.languages import LANGUAGE_CODE_EN
from bibleverses.models import MemoryStage, StageType, VerseSet
from scores.models import Scores

from .base import FullBrowserTest
from .test_bibleverses import RequireExampleVerseSetsMixin


def prepare_identity(sender, **kwargs):
    identity = kwargs['instance']
    identity.seen_help_tour = True


class LearnTests(RequireExampleVerseSetsMixin, FullBrowserTest):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    kjv_john_3_16 = "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life. John 3 16"

    psalm_23_1_2 = "The LORD is my shepherd I shall not want He maketh me to lie down in green pastures he leadeth me beside the still waters Psalm 23 1 2"

    def setUp(self):
        super().setUp()
        signals.pre_save.connect(prepare_identity, sender=Identity)

    def tearDown(self):
        signals.pre_save.disconnect(prepare_identity, sender=Identity)
        super().tearDown()

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
        # This is the number of words that will fail, given the
        # algo in _type_john_3_16_kjv:
        correct_word_count = math.floor(word_count * accuracy)

        # Copy algo in Learn.elm getTestResult:
        word_accuracies = ([1.0] * correct_word_count) + ([0.0] * (word_count - correct_word_count))
        actual_accuracy = float(round(sum(word_accuracies) / float(len(word_accuracies)) * 1000)) / 1000

        points_word_count = word_count - 3  # Don't get points for the reference
        return math.floor(Scores.points_per_word(LANGUAGE_CODE_EN) * points_word_count * actual_accuracy)

    def test_save_strength(self):
        verse_set = self.choose_verse_set('Bible 101')
        identity = self._get_current_identity()

        # Preconditions - should have been set up by choose_verse_set
        self.assertEqual(verse_set.verse_choices.count(), identity.verse_statuses.count())
        self.assertTrue(all(uvs.strength == Decimal('0.0') and
                            uvs.last_tested is None and
                            uvs.memory_stage == MemoryStage.ZERO
                            for uvs in identity.verse_statuses.all()))

        self.assertEqual("John 3:16", self.get_element_text("#id-verse-header h2"))
        # Do the reading:
        for i in range(0, 9):
            self.click("#id-next-btn")

        # Do the typing:
        self._type_john_3_16_kjv()

        self.wait_for_ajax()

        # Check the strength
        uvs = identity.verse_statuses.get(localized_reference='John 3:16')
        self.assertEqual(uvs.strength, MM.INITIAL_STRENGTH_FACTOR)

    def test_typing_verse_combo(self):
        identity, account = self.create_account()
        self.login(account)

        identity.add_verse_choice('Psalm 23:1-2')
        self.get_url('dashboard')
        self.submit('input[name=learnbiblequeue]')
        self.assertEqual("Psalm 23:1-2", self.get_element_text("#id-verse-header h2"))

        # Do the reading:
        for i in range(0, 9):
            self.click("#id-next-btn")

        self.wait_for_ajax()

        # Do the typing: The fixture has 'The Lord is my shepherd--I shall not
        # want' in order to test an issue with word splitting
        for word in self.psalm_23_1_2.strip().split():
            self.fill({"#id-typing": word + " "})

        self.wait_for_ajax()
        # Check the strength
        uvs = identity.verse_statuses.get(localized_reference='Psalm 23:1-2')
        self.assertEqual(uvs.strength, MM.INITIAL_STRENGTH_FACTOR)

        # Check the score
        points_for_verse = (
            Scores.points_per_word(LANGUAGE_CODE_EN) *
            (len(self.psalm_23_1_2.strip().split()) -
             4))  # don't count reference

        account = Account.objects.get(id=account.id)
        self.assertEqual(account.total_score.points,
                         points_for_verse +
                         points_for_verse * Scores.PERFECT_BONUS_FACTOR +
                         StudentAward(count=1).points() +
                         AceAward(count=1).points()
                         )

    def test_points_and_awards(self):
        identity, account = self.create_account()
        self.login(account)
        self.choose_verse_set('Bible 101')

        # Do the reading:
        for i in range(0, 9):
            self.click("#id-next-btn")

        # Do the typing:
        self._type_john_3_16_kjv()

        # Check scores
        time.sleep(0.5)
        j316_score = self._score_for_j316()
        account = Account.objects.get(id=account.id)
        self.assertEqual(account.total_score.points,
                         j316_score +
                         (j316_score * Scores.PERFECT_BONUS_FACTOR) +
                         StudentAward(count=1).points() +
                         AceAward(count=1).points()
                         )
        self.assertEqual(account.action_logs.count(), 4)

        # Check awards
        self.assertEqual(account.awards.filter(award_type=AwardType.ACE,
                                               level=1).count(), 1)
        self.assertEqual(account.awards.filter(award_type=AwardType.STUDENT,
                                               level=1).count(), 1)
        self.assertEqual(account.action_logs.filter(award__award_type=AwardType.ACE).count(),
                         1)
        self.assertEqual(account.action_logs.filter(award__award_type=AwardType.STUDENT).count(),
                         1)

        # Go back to dashboard, and should see message
        self.get_url('dashboard')
        self.assertTextPresent("You've earned a new badge")

    def test_review_passage_mixed(self):
        # Test reviewing a passage when some verses are to be tested and others
        # are just being read.
        identity, account = self.create_account()
        self.login(account)

        self.add_verse_set('Psalm 23')

        for i in range(1, 7):
            identity.record_verse_action('Psalm 23:%d' % i, 'KJV', StageType.TEST,
                                         1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(localized_reference='Psalm 23:1'))

        self.get_url('dashboard')
        self.submit('input[name=reviewpassage]')

        for word in "The LORD is my shepherd, I shall not want.".split():
            self.fill({"#id-typing": word + " "})

        # Test keyboard shortcut
        self.send_keys('button.primary', '\n')
        self.assertIn("He maketh me to lie down in green pastures",
                      self.get_element_text('.current-verse'))

        for i in range(0, 5):
            self.click("#id-next-btn")
        self.assertUrlsEqual(reverse('dashboard'))

    def test_skip_verse(self):
        self.choose_verse_set('Bible 101')

        self.assertEqual("John 3:16", self.get_element_text("#id-verse-header h2"))

        self.click("#id-verse-options-menu-btn")
        self.click("#id-skip-verse-btn")

        self.assertEqual("John 14:6", self.get_element_text("#id-verse-header h2"))

        # Should be removed from session too
        self.get_url('learn')

        self.assertEqual("John 14:6", self.get_element_text("#id-verse-header h2"))

    def test_cancel_learning(self):
        self.add_verse_set('Bible 101')

        identity = self._get_current_identity()
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        identity.record_verse_action('John 14:6', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses)

        # Go to dashboard
        self.get_url('dashboard')
        self.choose_review_bible()

        self.assertEqual("John 3:16", self.get_element_text("#id-verse-header h2"))

        self.click("#id-verse-options-menu-btn")
        self.click("#id-cancel-learning-btn")

        # Should skip.
        self.assertEqual("John 14:6", self.get_element_text("#id-verse-header h2"))

        # If we go back to dashboard and choose again, it should not appear
        # Go to dashboard
        self.get_url('dashboard')
        self.choose_review_bible()

        self.assertEqual("John 14:6", self.get_element_text("#id-verse-header h2"))

    def test_reset_progress(self):
        self.add_verse_set('Bible 101')
        identity = self._get_current_identity()
        # Ensure that we have seen some verses
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)
        self._make_verses_due_for_testing(identity.verse_statuses)

        self.get_url('dashboard')
        self.choose_review_bible()

        self.assertEqual("John 3:16", self.get_element_text("#id-verse-header h2"))

        self.click("#id-verse-options-menu-btn")
        self.click_and_confirm("#id-reset-progress-btn")

        # Should reset strength to zero
        self.assertEqual(identity.verse_statuses.get(localized_reference='John 3:16').strength,
                         0)
        # Should revert to initial read mode
        self.assertIn("READ", self.get_element_text('#id-instructions'))

    def choose_review_bible(self):
        self.submit("input[name='reviewbiblequeue']")

    def _make_verses_due_for_testing(self, uvs_queryset):
        n = timezone.now()
        uvs_queryset.update(
            last_tested=n - timedelta(200),
            next_test_due=n - timedelta(100),
        )

    def test_more_practice(self):
        # tests that the 'more practice' button appears, and works

        identity, account = self.create_account()
        self.login(account)
        self.add_verse_set('Bible 101')

        # Learn one
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(memory_stage=MemoryStage.TESTED))

        self.get_url('dashboard')
        self.choose_review_bible()

        self._type_john_3_16_kjv(accuracy=0.8)

        # Now the 'more practice' button will appear, and be primary
        self.assertIn('primary', self.get_element_attribute("#id-more-practice-btn", 'class').split())
        self.click("#id-more-practice-btn")

        # Now go through 4 stages:
        for i in range(0, 4):
            self.assertEqual(self.get_element_attribute("#id-next-btn", "disabled"),
                             None)
            self.click("#id-next-btn")

        self._type_john_3_16_kjv(accuracy=0.95)

        # We should get points for first time reviewed (and award)
        j316_score_1 = self._score_for_j316(accuracy=0.8)
        account = Account.objects.get(id=account.id)  # refresh
        self.assertEqual(account.total_score.points,
                         j316_score_1 +
                         StudentAward(count=1).points()
                         )
        self.assertEqual(account.action_logs.count(), 2)

    def test_hint_button(self):
        identity, account = self.create_account()
        self.login(account)
        self.add_verse_set('Bible 101')

        # Learn one
        identity.record_verse_action('John 3:16', 'KJV', StageType.TEST, 1.0)

        self._make_verses_due_for_testing(identity.verse_statuses.filter(memory_stage=MemoryStage.TESTED))

        self.get_url('dashboard')
        self.choose_review_bible()
        for i in range(0, 4):
            self.assertEqual(self.get_element_attribute("#id-hint-btn", "disabled"),
                             None)

            self.click("#id-hint-btn")

        # Hint button should be disabled after 3 clicks
        self.assertEqual(self.get_element_attribute("#id-hint-btn", "disabled"),
                         'true')
