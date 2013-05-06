from __future__ import absolute_import

from autofixture import AutoFixture
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from bibleverses.models import VerseSet, VerseSetType, TextVersion, quick_find

class SearchTests(TestCase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        self.account = AutoFixture(Account).create(1)[0]

    def test_search_verse_set_title(self):
        vs1 = VerseSet.objects.create(name="For stupid people",
                                      slug="for-stupid-people",
                                      public=True,
                                      set_type=VerseSetType.SELECTION,
                                      created_by=self.account)
        vs2 = VerseSet.objects.create(name="For intelligent people",
                                      slug="for-intelligent-people",
                                      public=True,
                                      set_type=VerseSetType.SELECTION,
                                      created_by=self.account)

        results = VerseSet.objects.search(VerseSet.objects.all(),
                                          "Stupid")
        self.assertEqual(len(results), 1)
        self.assertIn("For stupid people", (v.name for v in results))

    def test_search_verse_set_verses(self):
        vs1 = VerseSet.objects.create(name="A selection",
                                      slug="a-selection",
                                      public=True,
                                      set_type=VerseSetType.SELECTION,
                                      created_by=self.account)
        vs1.set_verse_choices([
                "Genesis 1:1",
                "Genesis 1:2",
                "John 3:16",
                ])

        results = VerseSet.objects.search(VerseSet.objects.all(),
                                          "Gen 1:3")
        self.assertEqual(len(results), 0)

        results = VerseSet.objects.search(VerseSet.objects.all(),
                                          "Gen 1:1")
        self.assertEqual(len(results), 1)
        self.assertEqual(list(results), [vs1])

    def test_quick_find_song_of_solomon(self):
        version = TextVersion.objects.get(slug='KJV')
        results = quick_find('Song of Solomon 1:1', version)
        self.assertEqual(results[0].verses[0].reference,
                         "Song of Solomon 1:1")
