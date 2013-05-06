from __future__ import absolute_import

from autofixture import AutoFixture
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from accounts.models import Account
from bibleverses.models import VerseSet, VerseSetType, TextVersion, quick_find, parse_as_bible_reference

class SearchTests(TestCase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        self.account = AutoFixture(Account).create(1)[0]
        c = connection.cursor()
        c.execute("CREATE INDEX bibleverses_verse_tsv_index ON bibleverses_verse USING gin(text_tsv);")
        c.execute("UPDATE bibleverses_verse SET text_tsv = to_tsvector(text);")


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

    def test_quick_find_book_names_as_searches(self):
        # Need to be able to find words that happen to be in the names of books.
        version = TextVersion.objects.get(slug='NET')
        results = quick_find("James", version, allow_searches=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].verses[0].reference,
                         "Matthew 4:21")

    def test_parse_as_bible_reference(self):
        self.assertEqual(None, parse_as_bible_reference("Matthew", allow_whole_book=False))
        self.assertNotEqual(None, parse_as_bible_reference("Matthew", allow_whole_book=True))
        self.assertEqual(None, parse_as_bible_reference("Matthew 1", allow_whole_chapter=False))
        self.assertNotEqual(None, parse_as_bible_reference("Matthew 1", allow_whole_chapter=True))

