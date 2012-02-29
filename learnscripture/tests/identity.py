from __future__ import absolute_import

from datetime import timedelta
import time

from django.test import TestCase
from django.utils import timezone

from accounts.models import Identity, ActionChange, Account
from bibleverses.models import VerseSet, BibleVersion, StageType, MemoryStage
from scores.models import Scores


class IdentityTests(TestCase):

    fixtures = ['test_bible_versions.json', 'test_verse_sets.json', 'test_bible_verses.json']

    def _create_identity(self):
        NET = BibleVersion.objects.get(slug='NET')
        return Identity.objects.create(default_bible_version=NET)

    def test_add_verse_set(self):
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        uvss = i.verse_statuses.all()
        self.assertEqual(len(uvss), len(vs1.verse_choices.all()))

        self.assertEqual(set(u.reference for u in uvss),
                         set(["John 3:16", "John 14:6"]))


        vs1 = VerseSet.objects.get(name='Bible 101') # fresh
        # Having already created the UserVerseStatuses, this should be an
        # efficient operation:
        with self.assertNumQueries(4):
            # 1 for existing uvs, same version
            # 1 for other versions.
            # 1 for verse_choices.all()
            # 1 for VerseSet.objects.mark_chosen
            uvss = i.add_verse_set(vs1)
            # session.set_verse_statuses will use all these:
            l = [(uvs.reference, uvs.verse_set_id)
                 for uvs in uvss]


    def test_record_read(self):
        i = self._create_identity()
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
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)

        vs2 = VerseSet.objects.get(name='Basic Gospel')
        i.add_verse_set(vs2)

        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              verse_set=vs2).memory_stage,
                         MemoryStage.SEEN)

    def test_record_doesnt_decrease_stage(self):
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)
        i.record_verse_action('John 3:16', 'NET', StageType.TEST, 1)
        self.assertEqual(i.verse_statuses.get(reference='John 3:16',
                                              version__slug='NET').memory_stage,
                         MemoryStage.TESTED)

    def test_record_against_verse_in_multiple_sets(self):
        # Setup
        i = self._create_identity()
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

    def test_change_version(self):
        # Setup
        i = self._create_identity()
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
        i = self._create_identity()
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
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        i.change_version('John 3:16', 'KJV', vs1.id)

        vs2 = VerseSet.objects.get(name='Basic Gospel')
        uvss = i.add_verse_set(vs2)
        self.assertEqual(i.verse_statuses.get(verse_set=vs2,
                                              reference='John 3:16').version.slug,
                         'KJV')

    def test_change_version_passage_set(self):
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Psalm 23')
        i.add_verse_set(vs1)
        i.change_version('Psalm 23:1', 'KJV', vs1.id)
        self.assertEqual([u'KJV'] * 6, [uvs.version.slug for uvs in i.verse_statuses.filter(verse_set=vs1)])


    def test_passages_for_learning(self):
        i = self._create_identity()
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
        # sneak a test for verse_statuses_for_revising() here
        self.assertEqual([], list(i.verse_statuses_for_revising()))

        # Sneak a test for passages_for_revising() here:
        self.assertEqual([], list(i.passages_for_revising()))

    def test_passages_for_revising(self):
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Psalm 23')
        i.add_verse_set(vs1)

        for vn in range(1, 7):
            ref = 'Psalm 23:%d' % vn
            i.record_verse_action(ref, 'NET', StageType.TEST, 1.0)
            # Put each one back by n days i.e. as if running over
            # multiple days
            i.verse_statuses.filter(reference=ref).update(
                last_tested=timezone.now() - timedelta(7 - vn))

            # Now test again, for all but the first
            if vn != 1:
                i.record_verse_action(ref, 'NET', StageType.TEST, 1.0)

        # Shouldn't be in general revision queue
        self.assertEqual([], list(i.verse_statuses_for_revising()))

        verse_sets = i.passages_for_revising()
        self.assertEqual(verse_sets[0].id, vs1.id)

    def test_verse_statuses_for_passage(self):
        i = self._create_identity()
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
            .update(strength=0.7, last_tested=now)

        # Move one of them back to needing testing
        i.verse_statuses.filter(reference="Psalm 23:3")\
            .update(last_tested=now - timedelta(1000))

        l = i.verse_statuses_for_passage(vs1.id)
        for uvs in l:
            self.assertEqual(uvs.needs_testing_by_strength, uvs.reference == "Psalm 23:3")
            self.assertEqual(uvs.needs_testing, True)

    def test_get_verse_statuses(self):
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Psalm 23')
        i.add_verse_set(vs1)

        with self.assertNumQueries(2):
            d = i.get_verse_statuses_bulk([(vs1.id, 'Psalm 23:1'),
                                           (vs1.id, 'Psalm 23:2'),
                                           (vs1.id, 'Psalm 23:3'),
                                           (vs1.id, 'Psalm 23:4'),
                                           (vs1.id, 'Psalm 23:5'),
                                           (vs1.id, 'Psalm 23:6')])

            self.assertEqual(d[vs1.id, 'Psalm 23:1'].reference, 'Psalm 23:1')
            texts = [uvs.text for uvs in d.values()]

        vs2 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs2)
