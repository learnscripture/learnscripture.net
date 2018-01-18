from django.urls import reverse

from accounts.models import Account, Identity
from bibleverses.models import StageType, VerseSet, VerseSetType
from groups.models import Group
from learnscripture.tests.base import TestBase
from scores.models import ScoreReason, get_verses_finished_count, get_verses_started_counts, get_verses_started_per_day

from .base import AccountTestMixin


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


class VerseCountTests(AccountTestMixin, TestBase):

    fixtures = AccountTestMixin.fixtures + ['test_bible_verses.json']

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

    def test_verses_started_dedupe(self):
        """
        Test that counts for verses started deduplicate verses that have the
        same localized_reference.
        """
        i, account = self.create_account()
        version = i.default_bible_version
        vs1, vs2 = self._create_overlapping_verse_sets(account)

        i.add_verse_set(vs1)
        i.add_verse_set(vs2)

        i.record_verse_action("Psalm 23:1", version.slug, StageType.TEST,
                              accuracy=1.0)
        dt = i.verse_statuses.filter(localized_reference="Psalm 23:1")[0].last_tested.date()

        self.assertEqual(get_verses_started_counts([i.id])[i.id], 1)

        self.assertEqual(get_verses_started_per_day(i.id),
                         [(dt, 1)])

    def test_verses_finished_dedupe(self):
        """
        Test that counts for verses finished deduplicate verses that have the
        same localized_reference.
        """
        i, account = self.create_account()
        version = i.default_bible_version
        vs1, vs2 = self._create_overlapping_verse_sets(account)

        i.add_verse_set(vs1)
        i.add_verse_set(vs2)

        i.record_verse_action("Psalm 23:1", version.slug, StageType.TEST,
                              accuracy=1.0)
        # Sanity check the test
        self.assertEqual(i.verse_statuses.filter(localized_reference="Psalm 23:1").count(),
                         2)
        i.verse_statuses.filter(localized_reference="Psalm 23:1").update(strength=0.9999)

        self.assertEqual(get_verses_finished_count(i.id, account.id), 1)
