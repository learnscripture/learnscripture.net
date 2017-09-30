from bibleverses.languages import LANGUAGE_CODE_EN
from bibleverses.models import TextVersion, Verse, VerseSet, VerseSetType, quick_find

from .base import TestBase, get_or_create_any_account


class SearchTests(TestBase):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(SearchTests, self).setUp()
        self.account = get_or_create_any_account()
        Verse.objects.all().update_text_search()

    def test_search_verse_set_title(self):
        VerseSet.objects.create(name="For stupid people",
                                slug="for-stupid-people",
                                public=True,
                                set_type=VerseSetType.SELECTION,
                                created_by=self.account)
        VerseSet.objects.create(name="For intelligent people",
                                slug="for-intelligent-people",
                                public=True,
                                set_type=VerseSetType.SELECTION,
                                created_by=self.account)

        results = VerseSet.objects.search(LANGUAGE_CODE_EN,
                                          VerseSet.objects.all(),
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

        results = VerseSet.objects.search(LANGUAGE_CODE_EN,
                                          VerseSet.objects.all(),
                                          "Gen 1:3")
        self.assertEqual(len(results), 0)

        results = VerseSet.objects.search(LANGUAGE_CODE_EN,
                                          VerseSet.objects.all(),
                                          "Gen 1:1")
        self.assertEqual(len(results), 1)
        self.assertEqual(list(results), [vs1])

    def test_quick_find_text(self):
        version = TextVersion.objects.get(slug='KJV')
        results = quick_find("beginning created", version=version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Genesis 1:1")

    def test_quick_find_escape(self):
        version = TextVersion.objects.get(slug='KJV')
        results = quick_find("beginning & | created", version=version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Genesis 1:1")
        results = quick_find("Genesissss 1:1", version=version)
        self.assertEqual(len(results), 0)
        results = quick_find("Hello!", version=version)
        self.assertEqual(len(results), 0)

    def test_quick_find_song_of_solomon(self):
        version = TextVersion.objects.get(slug='KJV')
        results = quick_find('Song of Solomon 1:1', version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Song of Solomon 1:1")

    def test_quick_find_numbered_book(self):
        version = TextVersion.objects.get(slug='KJV')
        results = quick_find("1 Corinthians 1:3", version=version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "1 Corinthians 1:3")

    def test_quick_find_book_names_as_searches(self):
        # Need to be able to find words that happen to be in the names of books.
        version = TextVersion.objects.get(slug='NET')
        results = quick_find("James", version, allow_searches=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Matthew 4:21")

    def test_quick_find_passage_mode(self):
        version = TextVersion.objects.get(slug='KJV')
        self.assertNotEqual(None, quick_find("Genesis 1:1-2:2", version, allow_searches=False,
                                             max_length=1000,
                                             ))
