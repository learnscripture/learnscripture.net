from django.test import TestCase

from accounts.models import Identity
from bibleverses.models import VerseSet, BibleVersion, StageType, MemoryStage

class IdentityTests(TestCase):

    fixtures = ['test_verse_sets.json']

    def _create_identity(self):
        NET = BibleVersion.objects.get(slug='NET')
        return Identity.objects.create(default_bible_version=NET)

    def test_add_verse_set(self):
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        uvss = i.verse_statuses.all()
        self.assertEqual(len(uvss), len(vs1.verse_choices.all()))

        self.assertEqual(set(u.verse_choice.reference for u in uvss),
                         set(["John 3:16", "John 14:6"]))


    def test_record_read(self):
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              version__slug='NET').memory_stage,
                         MemoryStage.ZERO)

        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              version__slug='NET').memory_stage,
                         MemoryStage.SEEN)

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

        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              verse_choice__verse_set=vs2).memory_stage,
                         MemoryStage.SEEN)

    def test_record_doesnt_decrease_stage(self):
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)
        i.record_verse_action('John 3:16', 'NET', StageType.TEST_TYPE_FULL, 1)
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              version__slug='NET').memory_stage,
                         MemoryStage.TESTED)

    def test_record_against_verse_in_multiple_sets(self):
        # Setup
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        vs2 = VerseSet.objects.get(name='Basic Gospel')
        i.add_verse_set(vs2)

        self.assertEqual(i.verse_statuses.filter(verse_choice__reference='John 3:16').count(),
                         2)
        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)

        # Test
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              verse_choice__verse_set=vs1).memory_stage,
                         MemoryStage.SEEN)
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              verse_choice__verse_set=vs2).memory_stage,
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
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              ignored=False,
                                              verse_choice__verse_set=vs1).version.slug,
                         'KJV')

        # The status should be reset.
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              ignored=False,
                                              verse_choice__verse_set=vs1).memory_stage,
                         MemoryStage.ZERO)

        # The status for the other verse set should have changed too,
        # because it is confusing otherwise
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              ignored=False,
                                              verse_choice__verse_set=vs2).version.slug,
                         'KJV')
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              ignored=False,
                                              verse_choice__verse_set=vs2).memory_stage,
                         MemoryStage.ZERO)

    def test_change_version_and_back(self):
        # Setup
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)

        i.record_verse_action('John 3:16', 'NET', StageType.READ, 1)
        i.change_version('John 3:16', 'KJV', vs1.id)
        i.change_version('John 3:16', 'NET', vs1.id)

        # Should remember the old MemoryStage
        self.assertEqual(i.verse_statuses.get(verse_choice__reference='John 3:16',
                                              ignored=False,
                                              verse_choice__verse_set=vs1).memory_stage,
                         MemoryStage.SEEN)

    def test_change_version_and_choose_again(self):
        """
        Check that is we change version for a verse and then add
        it via a different verse set, our change is remembered for new set.
        """
        # Setup
        i = self._create_identity()
        vs1 = VerseSet.objects.get(name='Bible 101')
        i.add_verse_set(vs1)
        i.change_version('John 3:16', 'KJV', vs1.id)

        vs2 = VerseSet.objects.get(name='Basic Gospel')
        uvss = i.add_verse_set(vs2)
        self.assertEqual(i.verse_statuses.get(verse_choice__verse_set=vs2,
                                              verse_choice__reference='John 3:16').version.slug,
                         'KJV')

    def test_change_version_passage_set(self):
        pass # TODO
