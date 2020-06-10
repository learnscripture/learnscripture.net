# -*- coding: utf-8 -*-
from datetime import timedelta

from django.urls import reverse

from accounts.memorymodel import MM
from accounts.models import Account, Identity
from bibleverses.models import MemoryStage, StageType, TextVersion, VerseSet, VerseSetType
from groups.models import Group
from learnscripture.tests.base import TestBase
from scores.models import ScoreReason, get_verses_finished_count, get_verses_started_counts, get_verses_started_per_day

from .base import AccountTestMixin, BibleVersesMixin, CatechismsMixin


class LeaderboardTests(TestBase):

    def setUp(self):
        super(LeaderboardTests, self).setUp()
        a1 = Account.objects.create(username='testuser1',
                                    email='test2@test.com')
        Identity.objects.create(account=a1)
        a1.add_points(100, ScoreReason.VERSE_TESTED)
        a2 = Account.objects.create(username='testuser2',
                                    email='test2@test.com',
                                    is_active=False)
        Identity.objects.create(account=a2)
        a2.add_points(50, ScoreReason.VERSE_TESTED)
        self.a1 = a1
        self.a2 = a2
        group = Group.objects.create(name='My group',
                                     slug='my-group',
                                     created_by=a1,
                                     open=True,
                                     public=True)
        group.add_user(a1)
        group.add_user(a2)
        self.group = group

    def test_get(self):
        resp = self.client.get(reverse('group_leaderboard', args=(self.group.slug,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.a1.username)
        self.assertNotContains(resp, self.a2.username)

    def test_get_thisweek(self):
        resp = self.client.get(reverse('group_leaderboard', args=(self.group.slug,)), {'thisweek': '1'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.a1.username)
        self.assertNotContains(resp, self.a2.username)


class VerseCountTests(BibleVersesMixin, CatechismsMixin, AccountTestMixin, TestBase):

    def test_catechisms(self):
        identity, account = self.create_account()
        c = TextVersion.objects.get(slug='WSC')
        identity.add_catechism(c)
        self._do_assert_stats(identity, 2, refs=['Q1', 'Q2'])

    def _create_overlapping_verse_sets(self, account):
        vs1 = VerseSet.objects.create(name="Psalm 23:1-3",
                                      language_code='en',
                                      set_type=VerseSetType.PASSAGE,
                                      created_by=account)
        vs2 = VerseSet.objects.create(name="Psalm 23:1-2",
                                      language_code='en',
                                      set_type=VerseSetType.PASSAGE,
                                      created_by=account)
        vs1.set_verse_choices(["BOOK18 23:1",
                               "BOOK18 23:2",
                               "BOOK18 23:3"])
        vs2.set_verse_choices(["BOOK18 23:1",
                               "BOOK18 23:2"])

        return vs1, vs2

    def test_verse_stats_dedupe(self):
        """
        Test that counts for verses started deduplicate verses that have the
        same localized_reference.
        """
        identity, account = self.create_account()
        vs1, vs2 = self._create_overlapping_verse_sets(account)

        identity.add_verse_set(vs1)
        identity.add_verse_set(vs2)

        # Sanity check the test
        self.assertEqual(identity.verse_statuses.filter(localized_reference="Psalm 23:1").count(),
                         2)

        self._do_assert_stats(identity, 1, refs=['Psalm 23:1'])

    def _do_assert_stats(self, identity: Identity, count, refs=None):
        if refs is None:
            ref_pairs = [(r.localized_reference, r.version) for r in identity.verse_statuses.all()]
            refs = [r for r, v in ref_pairs]
        else:
            ref_pairs = [(r.localized_reference, r.version)
                         for r in identity.verse_statuses.filter(localized_reference__in=refs)]

        for ref, version in ref_pairs:
            identity.record_verse_action(ref, version.slug, StageType.TEST,
                                         accuracy=1.0)

        # Started
        self.assertEqual(get_verses_started_counts([identity.id])[identity.id], count)

        # Started per day
        dt = identity.verse_statuses.filter(localized_reference__in=refs).first().last_tested.date()
        self.assertEqual(get_verses_started_per_day(identity.id),
                         [(dt, count)])

        # Move time on enough so that next hit gets past learnt threshold.
        identity.verse_statuses.update(strength=MM.LEARNT - 0.01)
        self.move_clock_on(timedelta(days=400))

        for ref, version in ref_pairs:
            # Simulate enough to get to 'learnt' state.
            action_change = identity.record_verse_action(ref, version.slug, StageType.TEST, accuracy=1)
            uvs = identity.verse_statuses.filter(localized_reference=ref, version=version).first()
            identity.award_action_points(ref,
                                         version.language_code,
                                         uvs.scoring_text,
                                         MemoryStage.TESTED,
                                         action_change,
                                         StageType.TEST,
                                         1)

        # Finished
        self.assertEqual(get_verses_finished_count(identity.id), count)

        # Finished since
        last_tested = identity.verse_statuses.filter(localized_reference__in=refs).first().last_tested
        self.assertEqual(get_verses_finished_count(
            identity.id,
            finished_since=last_tested + timedelta(seconds=10)
        ), 0)

        self.assertEqual(get_verses_finished_count(
            identity.id,
            finished_since=last_tested - timedelta(seconds=10)
        ), count)

    def test_verse_stats_merged(self):
        identity, account = self.create_account(version_slug='TCL02')
        version = identity.default_bible_version
        # Merged verse. We count as multiple for parity with
        # translations that don't have merged verses.
        identity.add_verse_choice('Romalılar 3:25-26', version)
        identity.record_verse_action('Romalılar 3:25-26', version.slug, StageType.TEST,
                                     accuracy=1.0)

        self._do_assert_stats(identity, 2)

    def test_verse_stats_combos(self):
        identity, account = self.create_account()
        version = identity.default_bible_version
        # Combo verse.
        identity.add_verse_choice('Psalm 23:1-2', version)
        identity.record_verse_action('Psalm 23:1-2', version.slug, StageType.TEST,
                                     accuracy=1.0)

        self._do_assert_stats(identity, 2)

    def test_verse_stats_combos_2(self):
        identity, account = self.create_account()
        version = identity.default_bible_version
        # Combo verse.
        identity.add_verse_choice('Psalm 23:1-2', version)
        identity.record_verse_action('Psalm 23:1-2', version.slug, StageType.TEST,
                                     accuracy=1.0)
        # Adding the same ones individually doesn't change anything
        identity.add_verse_choice('Psalm 23:1', version)
        identity.add_verse_choice('Psalm 23:2', version)
        identity.record_verse_action('Psalm 23:1', version.slug, StageType.TEST,
                                     accuracy=1.0)
        identity.record_verse_action('Psalm 23:2', version.slug, StageType.TEST,
                                     accuracy=1.0)

        self._do_assert_stats(identity, 2)
