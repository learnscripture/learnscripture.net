# -*- coding: utf-8 -*-
from django_ftl import override

from bibleverses.languages import LANGUAGE_CODE_EN, LANGUAGE_CODE_TR
from bibleverses.models import TextVersion, VerseSet, VerseSetType, quick_find

from .base import TestBase, get_or_create_any_account


class SearchTestsMixin(object):

    fixtures = ['test_bible_versions.json', 'test_bible_verses.json']

    def setUp(self):
        super(SearchTestsMixin, self).setUp()
        self.KJV = TextVersion.objects.get(slug='KJV')
        self.NET = TextVersion.objects.get(slug='NET')
        self.TCL02 = TextVersion.objects.get(slug='TCL02')
        for tv in TextVersion.objects.all():
            tv.update_text_search(tv.verse_set.all())


class SearchTests(SearchTestsMixin, TestBase):
    def setUp(self):
        super().setUp()
        self.account = get_or_create_any_account()

    def test_search_verse_set_title(self):
        VerseSet.objects.create(name="For stupid people",
                                slug="for-stupid-people",
                                public=True,
                                language_code='en',
                                set_type=VerseSetType.SELECTION,
                                created_by=self.account)
        VerseSet.objects.create(name="For intelligent people",
                                slug="for-intelligent-people",
                                public=True,
                                language_code='en',
                                set_type=VerseSetType.SELECTION,
                                created_by=self.account)

        results = VerseSet.objects.all().search([LANGUAGE_CODE_EN],
                                                "Stupid")
        self.assertEqual(len(results), 1)
        self.assertIn("For stupid people", (v.name for v in results))

    def test_search_verse_set_verses(self):
        vs1 = VerseSet.objects.create(name="A selection",
                                      slug="a-selection",
                                      public=True,
                                      language_code='en',
                                      set_type=VerseSetType.SELECTION,
                                      created_by=self.account)
        vs1.set_verse_choices([
            "BOOK0 1:1",
            "BOOK0 1:2",
            "BOOK41 3:16",
        ])

        results = VerseSet.objects.all().search([LANGUAGE_CODE_EN],
                                                "Gen 1:3")
        self.assertEqual(len(results), 0)

        results = VerseSet.objects.all().search([LANGUAGE_CODE_EN],
                                                "Gen 1:1")
        self.assertEqual(len(results), 1)
        self.assertEqual(list(results), [vs1])

    def test_multi_language_search(self):
        vs1 = VerseSet.objects.create(name="Psalm 23",
                                      slug="psalm-23",
                                      public=True,
                                      language_code='en',
                                      set_type=VerseSetType.PASSAGE,
                                      created_by=self.account)
        vs1.set_verse_choices([
            "BOOK18 23:1",
            "BOOK18 23:2",
            "BOOK18 23:3",
            "BOOK18 23:4",
            "BOOK18 23:5",
            "BOOK18 23:6",
        ])

        vs2 = VerseSet.objects.create(name="Mezmur 23",
                                      slug="mezmur-23",
                                      public=True,
                                      language_code='tr',
                                      set_type=VerseSetType.PASSAGE,
                                      created_by=self.account)
        vs2.set_verse_choices([
            "BOOK18 23:1",
            "BOOK18 23:2",
            "BOOK18 23:3",
            "BOOK18 23:4",
            "BOOK18 23:5",
            "BOOK18 23:6",
        ])

        # Search verse refs single language
        results = VerseSet.objects.all().search([LANGUAGE_CODE_EN],
                                                "Psalm 23")
        self.assertEqual(list(results), [vs1])

        results2 = VerseSet.objects.all().search([LANGUAGE_CODE_TR],
                                                 "Mezmur 23")
        self.assertEqual(list(results2), [vs2])

        # Search verse refs multiple languages
        results3 = VerseSet.objects.all().search([LANGUAGE_CODE_EN, LANGUAGE_CODE_TR],
                                                 "Mz 23")
        self.assertEqual(set(results3), set([vs1, vs2]))

        # ... with default_language_code that matches verse refs:
        results4 = VerseSet.objects.all().search([LANGUAGE_CODE_EN, LANGUAGE_CODE_TR],
                                                 "Mz 23", default_language_code='tr')
        self.assertEqual(set(results4), set([vs1, vs2]))

        # ... and one that doesn't. Here the logic should fall back to parsing
        # 'Mz 23' as Turkish, because 'Mz 23' doesn't parse as a bible ref in English.
        results5 = VerseSet.objects.all().search([LANGUAGE_CODE_EN, LANGUAGE_CODE_TR],
                                                 "Mz 23", default_language_code='en')
        self.assertEqual(set(results5), set([vs1, vs2]))


class QuickFindTests(SearchTestsMixin, TestBase):

    def test_quick_find_text(self):
        version = self.KJV
        results, more = quick_find("beginning created", version=version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Genesis 1:1")

    def test_quick_find_text_turkish(self):
        version = self.TCL02
        # Testing for handling accents and stemming correctly.
        # 'siniz' should be dropped, and word with 'iz' ending
        # should be found.
        results, more = quick_find("övünebilirsiniz", version=version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Romalılar 3:27")
        self.assertIn("övünebiliriz", results[0].text)

    def test_quick_find_escape(self):
        version = self.KJV
        results, more = quick_find("beginning & | created", version=version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Genesis 1:1")
        results, more = quick_find("Genesissss 1:1", version=version)
        self.assertEqual(len(results), 0)
        results, more = quick_find("Hello!", version=version)
        self.assertEqual(len(results), 0)

    def test_quick_find_song_of_solomon(self):
        version = self.KJV
        results, more = quick_find('Song of Solomon 1:1', version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Song of Solomon 1:1")

    def test_quick_find_numbered_book(self):
        version = self.KJV
        results, more = quick_find("1 Corinthians 1:3", version=version)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "1 Corinthians 1:3")

    def test_quick_find_book_names_as_searches(self):
        # Need to be able to find words that happen to be in the names of books.
        version = self.NET
        results, more = quick_find("James", version, allow_searches=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].verses[0].localized_reference,
                         "Matthew 4:21")

    def test_quick_find_passage_mode(self):
        version = self.KJV
        results, more = quick_find("Genesis 1:1-2:2", version, allow_searches=False,
                                   max_length=1000)
        self.assertNotEqual(None, results)

    def test_quick_find_merged_verse(self):
        version = self.TCL02
        # There is no 3:25, 3:26 - rather there is 3:25-26
        refs = [("Romalılar 3:25", "Romalılar 3:25-26", 25, 26, 1, 1),
                ("Romalılar 3:26", "Romalılar 3:25-26", 25, 26, 1, 1),
                ("Romalılar 3:25-26", "Romalılar 3:25-26", 25, 26, 1, 2),
                ("Romalılar 3:24-25", "Romalılar 3:24-26", 24, 26, 2, 2),
                ("Romalılar 3:26-27", "Romalılar 3:25-27", 25, 27, 2, 2),
                ]
        for ref, corrected_ref, start_verse, end_verse, length, q in refs:
            with self.assertNumQueries(q):
                with override('en'):
                    results, more = quick_find(ref, version)
                v = results[0]
                # v is always a VerseSearchResult for quick_find results
                self.assertEqual(v.localized_reference, corrected_ref, "For ref " + ref)
                self.assertEqual(len(v.verses), length, "For ref " + ref)
                if length == 1:
                    self.assertEqual(v.verses[0].localized_reference, corrected_ref, "For ref " + ref)

                # Some tests for parsed_ref attribute that is used by
                # front end
                self.assertEqual(v.parsed_ref.start_verse, start_verse, "For ref " + ref)
                self.assertEqual(v.parsed_ref.end_verse, end_verse, "For ref " + ref)
