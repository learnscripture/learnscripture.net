from __future__ import absolute_import

from datetime import timedelta
import time

from django.db.models import F
from django.test import TestCase
from django.utils import timezone

import accounts.memorymodel
from awards.models import AwardType
from bibleverses.models import VerseSet, TextVersion, StageType, MemoryStage, Verse, VerseChoice
from events.models import Event, EventType

from .base import FuzzyInt, AccountTestMixin

__all__ = ['IdentityTests']


class IdentityTests(AccountTestMixin, TestCase):

    fixtures = AccountTestMixin.fixtures + ['test_verse_sets.json', 'test_bible_verses.json']

    def test_add_verse_set(self):
        i = self.create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        uvss = i.verse_statuses.all()
        self.assertEqual(len(uvss), len(vs1.verse_choices.all()))

        self.assertEqual(set(u.reference for u in uvss),
                         set(["John 3:16", "John 14:6"]))


        vs1 = VerseSet.objects.get(name='Bible 101') # fresh
        # Having already created the UserVerseStatuses, this should be an
        # efficient operation:
        with self.assertNumQueries(FuzzyInt(3, 7)):
            # 1 for existing uvs, same version
            # 1 for other versions.
            # possibly one for verse_choices_all(), depending on caching
            # 1 for VerseSet.popularity update
            # 3 for awards
            uvss = i.add_verse_set(vs1)
            # session.set_verse_statuses will use all these:
            [(uvs.reference, uvs.verse_set_id)
             for uvs in uvss]


    def test_record_read(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              version__slug='NET').memory_stage,
                         MemoryStage.ZERO)

        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)
        uvs = i.verse_statuses.get(reference='John 3:16',
                                   version__slug='NET')
        self.assertEqual(uvs.memory_stage, MemoryStage.SEEN)
        self.assertTrue(uvs.first_seen is not None)

        first_seen = uvs.first_seen
        time.sleep(1)
        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)
        uvs = i.verse_statuses.get(reference='John 3:16',
                                   version__slug='NET')
        # first_seen field should not have changed
        self.assertEqual(uvs.first_seen, first_seen)


    def test_add_verse_set_progress_and_choose_again(self):
        """
        Tests that if we choose a verse a second time after making progress with
        it already, the progress is remembered.
        """
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)

        vs2 = VerseSet.objects.get(name='Basic Gospel')
        i.add_verse_set(vs2)

        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              verse_set=vs2).memory_stage,
                         MemoryStage.SEEN)

    def test_record_doesnt_decrease_stage(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)
        i.record_verse_action('John 3:16', 'NET', StageType.TEST, 1)
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              version__slug='NET').memory_stage,
                         MemoryStage.TESTED)

    def test_record_against_verse_in_multiple_sets(self):
        # Setup
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        vs2 = VerseSet.objects.get(name='Basic Gospel')
        i.add_verse_set(vs2)

        self.assertEqual(i.verse_statuses.filter(reference='John 3:16').count(),
                         2)
        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)

        # Test
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              verse_set=vs1).memory_stage,
                         MemoryStage.SEEN)
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              verse_set=vs2).memory_stage,
                         MemoryStage.SEEN)

    def test_record_creates_awards(self):
        i, account = self.create_account(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        i.record_verse_action('John 3:16', 'NET', StageType.TEST, 1)
        # Check 'STUDENT'
        self.assertEqual(account.awards.filter(award_type=AwardType.STUDENT, level=1).count(),
                         1)
        # Check 'MASTER'
        # frig the data:
        i.verse_statuses.update(strength=accounts.memorymodel.MM.LEARNT - 0.001,
                                last_tested=timezone.now() - timedelta(100))
        # Now do test to move above LEARNT
        i.record_verse_action('John 3:16', 'NET', StageType.TEST, 1)
        self.assertEqual(account.awards.filter(award_type=AwardType.MASTER, level=1).count(),
                         1)

    def test_change_version(self):
        # Setup
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        vs2 = VerseSet.objects.get(name='Basic Gospel')
        i.add_verse_set(vs2)

        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)

        # Now change
        i.change_version('John 3:16', 'KJV', vs1.id)
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              ignored=False,
                                              verse_set=vs1).version.slug,
                         'KJV')

        # The status should be reset.
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              ignored=False,
                                              verse_set=vs1).memory_stage,
                         MemoryStage.ZERO)

        # The status for the other verse set should have changed too,
        # because it is confusing otherwise
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              ignored=False,
                                              verse_set=vs2).version.slug,
                         'KJV')
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              ignored=False,
                                              verse_set=vs2).memory_stage,
                         MemoryStage.ZERO)

    def test_change_version_and_back(self):
        # Setup
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        i.record_verse_action('John 3:16', 'NET', StageType.TEST, 1.0)
        i.change_version('John 3:16', 'KJV', vs1.id)
        i.change_version('John 3:16', 'NET', vs1.id)

        # Should remember the old MemoryStage
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              ignored=False,
                                              verse_set=vs1).memory_stage,
                         MemoryStage.TESTED)

    def test_change_version_and_choose_again(self):
        """
        Check that if we change version for a verse and then add
        it via a different verse set, our change is remembered for new set.
        """
        # Setup
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        i.change_version('John 3:16', 'KJV', vs1.id)

        vs2 = VerseSet.objects.get(name='Basic Gospel')
        i.add_verse_set(vs2)
        self.assertEqual(i.verse_statuses.get(verse_set=vs2,
                                              reference='John 3:16').version.slug,
                         'KJV')

    def test_change_version_passage_set(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Psalm 23')
        i.add_verse_set(vs1)
        i.change_version('Psalm 23:1', 'KJV', vs1.id)
        self.assertEqual([u'KJV'] * 6, [uvs.version.slug for uvs in i.verse_statuses.filter(verse_set=vs1)])

    def test_change_version_to_missing(self):
        """
        Attempts to change version when is missing in destination
        version should fail.
        """
        i = self.create_identity(version_slug='NET')
        KJV = TextVersion.objects.get(slug='KJV')
        i.add_verse_choice('John 3:16')

        uvs_list = list(i.verse_statuses.all())
        self.assertTrue(all(u.version.slug == 'NET' for u in uvs_list))

        KJV.verse_set.get(reference='John 3:16').mark_missing()
        replacements = i.change_version('John 3:16', 'KJV', None)
        self.assertEqual(replacements,
                         {uvs_list[0].id: uvs_list[0].id})

        self.assertEqual(list(i.verse_statuses.all()),
                         uvs_list)

    def test_bible_verse_statuses_for_revising(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        i.record_verse_action('John 3:16', 'NET', StageType.TEST, 1.0)

        # It should be set for revising yet
        self.assertEqual([], list(i.bible_verse_statuses_for_revising()))

        # It is confusing if it is ever ready within an hour, so we special case
        # that.

        # Fix data:
        i.verse_statuses.all().update(last_tested = timezone.now() - timedelta(0.99/24))

        self.assertEqual([], list(i.bible_verse_statuses_for_revising()))

    def test_passages_for_learning(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Psalm 23')
        i.add_verse_set(vs1)

        i.record_verse_action('Psalm 23:1', 'NET', StageType.TEST, 1.0)
        verse_sets = i.passages_for_learning()
        self.assertEqual(verse_sets[0].id, vs1.id)
        self.assertEqual(verse_sets[0].tested_total, 1)
        self.assertEqual(verse_sets[0].untested_total, 5)


        # Put it back so that it ought to be up for testing.
        i.verse_statuses.update(last_tested=timezone.now() - timedelta(10))

        # Shouldn't be in general revision queue -
        # sneak a test for bible_verse_statuses_for_revising() here
        self.assertEqual([], list(i.bible_verse_statuses_for_revising()))

        # Sneak a test for passages_for_revising() here:
        self.assertEqual([], list(i.passages_for_revising()))

    def test_passages_for_revising(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Psalm 23')
        i.add_verse_set(vs1)

        for vn in range(1, 7):
            ref = 'Psalm 23:%d' % vn
            i.record_verse_action(ref, 'NET', StageType.TEST, 1.0)
            # Put each one back by n days i.e. as if running over
            # multiple days
            i.verse_statuses.filter(reference=ref).update(
                last_tested=F('last_tested') - timedelta(7 - vn),
                next_test_due=F('next_test_due') - timedelta(7 - vn)
                )

            # Now test again, for all but the first
            if vn != 1:
                i.record_verse_action(ref, 'NET', StageType.TEST, 1.0)

        # Shouldn't be in general revision queue
        self.assertEqual([], list(i.bible_verse_statuses_for_revising()))

        verse_sets = i.passages_for_revising()
        self.assertEqual(verse_sets[0].id, vs1.id)

    def test_verse_statuses_for_passage(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Psalm 23')
        i.add_verse_set(vs1)

        l = i.verse_statuses_for_passage(vs1.id)

        self.assertEqual([uvs.reference for uvs in l],
                         [u"Psalm 23:1",
                          u"Psalm 23:2",
                          u"Psalm 23:3",
                          u"Psalm 23:4",
                          u"Psalm 23:5",
                          u"Psalm 23:6"])

        # Now test and age them:
        for uvs in l:
            i.record_verse_action(uvs.reference, 'NET', StageType.TEST, 1.0)

        now = timezone.now()
        i.verse_statuses.filter(reference__startswith="Psalm 23")\
            .update(strength=0.7,
                    last_tested=now,
                    next_test_due=now + timedelta(10)
                    )

        # Move one of them back to needing testing
        i.verse_statuses.filter(reference="Psalm 23:3").update(
            last_tested=now - timedelta(1000),
            next_test_due=now - timedelta(500)
            )

        l = i.verse_statuses_for_passage(vs1.id)
        for uvs in l:
            self.assertEqual(uvs.needs_testing_by_db, uvs.reference == "Psalm 23:3")
            self.assertEqual(uvs.needs_testing, True)

    def test_get_next_section(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Psalm 23')
        vs1.breaks = "3,5" # break at v3 and v5 - unrealistic!
        vs1.save()
        i.add_verse_set(vs1)

        for vn in range(1, 7):
            ref = 'Psalm 23:%d' % vn
            i.record_verse_action(ref, 'NET', StageType.TEST, 1.0)
            i.verse_statuses.filter(reference=ref).update(
                last_tested=F('last_tested') - timedelta(10),
                next_test_due=F('next_test_due') - timedelta(10),
                )

        # Shouldn't be splittable yet, since strength will be below threshold
        vss = i.passages_for_revising()
        self.assertEqual(len(vss), 1)
        self.assertEqual(vss[0].name, "Psalm 23")
        self.assertEqual(vss[0].splittable, False)

        for vn in range(1, 7):
            ref = 'Psalm 23:%d' % vn
            # Now, move each to beyond the threshold which triggers
            # group testing.
            # Put each 1 minute apart, to simulate having tested the whole
            # group together.
            for uvs in i.verse_statuses.filter(reference=ref):
                uvs.last_tested = timezone.now() - timedelta(200 - (vn * 60.0)/(3600.0*24))
                uvs.strength = 0.55
                uvs.next_test_due = accounts.memorymodel.next_test_due(uvs.last_tested, uvs.strength)
                uvs.save()

        vss = i.passages_for_revising()
        self.assertEqual(len(vss), 1)
        self.assertEqual(vss[0].name, "Psalm 23")
        self.assertEqual(vss[0].splittable, True)

        # Now test verse_statuses_for_passage/get_next_section in this context:

        uvss1 = i.verse_statuses_for_passage(vs1.id)
        uvss1 = i.get_next_section(uvss1, vs1)

        # uvss should be first two verses only:
        self.assertEqual(["Psalm 23:1", "Psalm 23:2"],
                          [uvs.reference for uvs in uvss1])

        # Now if we learn these two...
        for uvs in uvss1:
            i.record_verse_action(uvs.reference, 'NET', StageType.TEST, 0.95)

        # ...then we should get the next two. But we also get a verse
        # of context.

        uvss2 = i.verse_statuses_for_passage(vs1.id)
        uvss2 = i.get_next_section(uvss2, vs1)

        self.assertEqual(["Psalm 23:2", "Psalm 23:3", "Psalm 23:4"],
                         [uvs.reference for uvs in uvss2])
        self.assertEqual([False, True, True],
                         [uvs.needs_testing for uvs in uvss2])

        # A sleep of one second will ensure our algo can distinguish
        # between groups of testing.
        time.sleep(1)

        # Learn next two.

        for uvs in uvss2:
            i.record_verse_action(uvs.reference, 'NET', StageType.TEST, 0.95)

        uvss3 = i.verse_statuses_for_passage(vs1.id)
        uvss3 = i.get_next_section(uvss3, vs1)

        self.assertEqual(["Psalm 23:4", "Psalm 23:5", "Psalm 23:6"],
                         [uvs.reference for uvs in uvss3])
        self.assertEqual([False, True, True],
                         [uvs.needs_testing for uvs in uvss3])


        # Learn next two.
        time.sleep(1)
        for uvs in uvss3:
            i.record_verse_action(uvs.reference, 'NET', StageType.TEST, 0.95)

        # Should wrap around now:
        uvss4 = i.verse_statuses_for_passage(vs1.id)
        uvss4 = i.get_next_section(uvss4, vs1)

        self.assertEqual(["Psalm 23:1", "Psalm 23:2"],
                          [uvs.reference for uvs in uvss4])


    def test_slim_passage_for_revising(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Psalm 23')
        vs1.breaks = "3,5" # break at v3 and v5
        vs1.save()
        i.add_verse_set(vs1)

        for vn in range(1, 7):
            ref = 'Psalm 23:%d' % vn
            i.record_verse_action(ref, 'NET', StageType.TEST, 1.0)

            # Make one of them needing testing
        i.verse_statuses.filter(reference="Psalm 23:5").update(
                next_test_due=timezone.now() - timedelta(1)
                )

        uvss = i.verse_statuses_for_passage(vs1.id)
        self.assertEqual(len(uvss), 6)

        uvss = i.slim_passage_for_revising(uvss, vs1)
        self.assertEqual([uvs.reference for uvs in uvss],
                         ["Psalm 23:4", "Psalm 23:5", "Psalm 23:6"])


    def test_get_verse_statuses(self):
        i = self.create_identity()
        vs1 = VerseSet.objects.get(name='Psalm 23')
        uvss = list(i.add_verse_set(vs1))

        with self.assertNumQueries(2):
            d = i.get_verse_statuses_bulk([uvs.id for uvs in uvss])
            self.assertEqual(d[uvss[1].id].reference, uvss[1].reference)
            [uvs.text for uvs in d.values()]

    def test_add_verse_choice_copies_strength(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Psalm 23')
        i.add_verse_set(vs1)

        i.record_verse_action('Psalm 23:1', 'NET', StageType.TEST, 1)
        self.assertNotEqual(i.verse_statuses.get(reference='Psalm 23:1').strength, 0)

        # Now use add_verse_choice
        i.add_verse_choice('Psalm 23:1')

        # We need two UserVerseStatuses, because the user wants to learn this
        # verse outside the context of the passage.
        self.assertEqual(i.verse_statuses.filter(reference='Psalm 23:1').count(), 2)

        self.assertFalse(0.0 in [uvs.strength for uvs in i.verse_statuses.filter(reference='Psalm 23:1')])


    def test_verses_started_milestone_event(self):
        # This reproduces a bit of the logic from ActionCompleteHandler in order
        # to test Identity.award_action_points

        i, account = self.create_account(version_slug='KJV')

        refs = \
            ['Genesis 1:%d' % j for j in range(1, 11)] + \
            ['Genesis 2:%d' % j for j in range(1, 3)]

        for j, ref in enumerate(refs):
            i.add_verse_choice(ref)
            action_change = i.record_verse_action(ref, 'KJV', StageType.TEST, 1)
            i.award_action_points(ref,
                                  Verse.objects.get(reference=ref, version__slug='KJV').text,
                                  MemoryStage.SEEN, action_change, StageType.TEST, 1)

            self.assertEqual(Event.objects.filter(event_type=EventType.VERSES_STARTED_MILESTONE).count(),
                             0 if j < 9 else 1)

    def test_verses_finished_milestone_event(self):
        i, account = self.create_account(version_slug='KJV')

        refs = \
            ['Genesis 1:%d' % j for j in range(1, 11)] + \
            ['Genesis 2:%d' % j for j in range(1, 3)]

        for j, ref in enumerate(refs):
            i.add_verse_choice(ref)
            i.record_verse_action(ref, 'KJV', StageType.TEST, 1)
            # Move to nearly learnt:
            i.verse_statuses.filter(reference=ref).update(
                strength=accounts.memorymodel.LEARNT - 0.001,
                last_tested=timezone.now() - timedelta(100)
                )
            # Final test, moving to above LEARNT
            action_change = i.record_verse_action(ref, 'KJV', StageType.TEST, 1)
            i.award_action_points(ref,
                                  Verse.objects.get(reference=ref, version__slug='KJV').text,
                                  MemoryStage.TESTED, action_change, StageType.TEST, 1)
            self.assertEqual(Event.objects.filter(event_type=EventType.VERSES_FINISHED_MILESTONE).count(),
                             0 if j < 9 else 1)

    def test_order_after_cancelling_and_re_adding_verse(self):
        """
        If a verse is added, then cancelled, then added again as part of a set,
        the order of learning should be the order defined in the set.
        """
        i = self.create_identity(version_slug='NET')
        i.add_verse_choice('John 14:6')
        self.assertEqual([uvs.reference for uvs in i.bible_verse_statuses_for_learning(None)],
                         ['John 14:6'])
        i.record_verse_action('John 14:6', 'NET', StageType.READ, 1)
        i.cancel_learning(['John 14:6'])
        time.sleep(1)

        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        self.assertEqual([uvs.reference for uvs in i.bible_verse_statuses_for_learning(vs1.id)],
                         ['John 3:16', 'John 14:6'])

    def test_issue_75(self):
        i = self.create_identity(version_slug='NET')
        vs1 = VerseSet.objects.get(name='Psalm 23')

        # Change it so that it misses the last verse
        vs1.set_verse_choices([u"Psalm 23:1",
                               u"Psalm 23:2",
                               u"Psalm 23:3",
                               u"Psalm 23:4",
                               u"Psalm 23:5"])

        # Now add it
        i.add_verse_set(vs1)

        l = i.verse_statuses_for_passage(vs1.id)
        self.assertEqual([uvs.reference for uvs in l],
                         [u"Psalm 23:1",
                          u"Psalm 23:2",
                          u"Psalm 23:3",
                          u"Psalm 23:4",
                          u"Psalm 23:5"])

        # Now learn a standalone verse choice
        i.add_verse_choice('Psalm 23:6')

        # Add the verse back to the set
        VerseChoice.objects.create(reference="Psalm 23:6",
                                   verse_set=vs1,
                                   set_order=6)

        # Now 'press' the learn button again
        i.add_verse_set(vs1)

        # Should have all verses this time
        l = i.verse_statuses_for_passage(vs1.id)
        self.assertEqual([uvs.reference for uvs in l],
                         [u"Psalm 23:1",
                          u"Psalm 23:2",
                          u"Psalm 23:3",
                          u"Psalm 23:4",
                          u"Psalm 23:5",
                          u"Psalm 23:6"])

    def test_add_missing_verse(self):
        """
        Should be able to create a UVS against a missing verse.
        """
        i = self.create_identity()
        version = i.default_bible_version
        version.verse_set.get(reference='John 3:16').mark_missing()
        i.add_verse_choice('John 3:16')
        self.assertEqual(
            i.verse_statuses.filter(reference='John 3:16',
                                    version=version).count(),
            0)


    def test_consistent_learner_award(self):
        import awards.tasks
        identity, account = self.create_account(version_slug='KJV')

        def learn(i):
            # We simulate testing over time by moving previous data back a day
            identity.verse_statuses.update(first_seen=F('first_seen') - timedelta(days=1))
            ref = "Genesis 1:%d" % i
            identity.add_verse_choice(ref)
            identity.record_verse_action(ref, 'KJV', StageType.TEST, 1.0)

        for i in range(1, 10):
            learn(i)
            # Simulate the cronjob that runs
            awards.tasks.give_all_consistent_learner_awards()

            self.assertEqual(account.awards.filter(award_type=AwardType.CONSISTENT_LEARNER).count(),
                             0 if i < 7 else 1)
