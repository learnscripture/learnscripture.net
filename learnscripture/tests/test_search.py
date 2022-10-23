from django_ftl import override

from bibleverses.languages import LANG, LANGUAGES
from bibleverses.models import POSTGRES_SEARCH_CONFIGURATIONS, TextVersion, VerseSet, VerseSetType, quick_find

from .base import BibleVersesMixin, TestBase, get_or_create_any_account


class SearchTestsMixin(BibleVersesMixin):
    def setUp(self):
        super().setUp()
        for tv in TextVersion.objects.all():
            tv.update_text_search(tv.verse_set.all())


class SearchTests(SearchTestsMixin, TestBase):
    """
    Tests for verse set search functionality
    """

    def setUp(self):
        super().setUp()
        self.account = get_or_create_any_account()

    def test_search_verse_set_title(self):
        VerseSet.objects.create(
            name="For stupid people",
            slug="for-stupid-people",
            public=True,
            language_code="en",
            set_type=VerseSetType.SELECTION,
            created_by=self.account,
        )
        VerseSet.objects.create(
            name="For intelligent people",
            slug="for-intelligent-people",
            public=True,
            language_code="en",
            set_type=VerseSetType.SELECTION,
            created_by=self.account,
        )

        results = VerseSet.objects.all().search([LANG.EN], "Stupid")
        assert len(results) == 1
        assert "For stupid people" in (v.name for v in results)

    def test_search_verse_set_verses(self):
        vs1 = VerseSet.objects.create(
            name="A selection",
            slug="a-selection",
            public=True,
            language_code="en",
            set_type=VerseSetType.SELECTION,
            created_by=self.account,
        )
        vs1.set_verse_choices(
            [
                "BOOK0 1:1",
                "BOOK0 1:2",
                "BOOK41 3:16",
            ]
        )

        results = VerseSet.objects.all().search([LANG.EN], "Gen 1:3")
        assert len(results) == 0

        results = VerseSet.objects.all().search([LANG.EN], "Gen 1:1")
        assert len(results) == 1
        assert list(results) == [vs1]

    def test_multi_language_search(self):
        vs1 = VerseSet.objects.create(
            name="Psalm 23 - my favorite",
            slug="psalm-23",
            public=True,
            language_code="en",
            set_type=VerseSetType.PASSAGE,
            created_by=self.account,
        )
        vs1.set_verse_choices(
            [
                "BOOK18 23:1",
                "BOOK18 23:2",
                "BOOK18 23:3",
                "BOOK18 23:4",
                "BOOK18 23:5",
                "BOOK18 23:6",
            ]
        )

        vs2 = VerseSet.objects.create(
            name="Mezmur 23 - en sevdiğim",
            slug="mezmur-23",
            public=True,
            language_code="tr",
            set_type=VerseSetType.PASSAGE,
            created_by=self.account,
        )
        vs2.set_verse_choices(
            [
                "BOOK18 23:1",
                "BOOK18 23:2",
                "BOOK18 23:3",
                "BOOK18 23:4",
                "BOOK18 23:5",
                "BOOK18 23:6",
            ]
        )

        # Search verse refs single language
        results = VerseSet.objects.all().search([LANG.EN], "Psalm 23")
        assert list(results) == [vs1]

        results2 = VerseSet.objects.all().search([LANG.TR], "Mezmur 23")
        assert list(results2) == [vs2]

        # Search verse refs multiple languages
        results3 = VerseSet.objects.all().search([LANG.EN, LANG.TR], "Mz 23")
        assert set(results3) == {vs1, vs2}

        # ... with default_language_code that matches verse refs:
        results4 = VerseSet.objects.all().search([LANG.EN, LANG.TR], "Mz 23", default_language_code="tr")
        assert set(results4) == {vs1, vs2}

        # ... and one that doesn't. Here the logic should fall back to parsing
        # 'Mz 23' as Turkish, because 'Mz 23' doesn't parse as a bible ref in English.
        results5 = VerseSet.objects.all().search([LANG.EN, LANG.TR], "Mz 23", default_language_code="en")
        assert set(results5) == {vs1, vs2}

    def test_any_language(self):
        # This should be treated as 'any language' because the name is translatable
        vs = VerseSet.objects.create(
            name="Psalm 23",
            slug="psalm-23",
            public=True,
            language_code="en",
            set_type=VerseSetType.PASSAGE,
            created_by=self.account,
        )
        vs.set_verse_choices(
            [
                "BOOK18 23:1",
                "BOOK18 23:2",
                "BOOK18 23:3",
                "BOOK18 23:4",
                "BOOK18 23:5",
                "BOOK18 23:6",
            ]
        )

        # and therefore found in a turkish only search:
        results = VerseSet.objects.all().search([LANG.TR], "Mezmur 23")
        assert list(results) == [vs]

        # But now only as English:
        vs.name = "Psalm 23 - my favourite"
        vs.save()

        results2 = VerseSet.objects.all().search([LANG.TR], "Mezmur 23")
        assert list(results2) == []

        results3 = VerseSet.objects.all().search([LANG.EN], "Psalm 23")
        assert list(results3) == [vs]

    def test_search_full_passage(self):
        vs1 = VerseSet.objects.create(
            name="The Lord is my shepherd",
            slug="the-lord-is-my-shepherd",
            public=True,
            language_code="en",
            set_type=VerseSetType.PASSAGE,
            created_by=self.account,
        )
        vs1.set_verse_choices(
            [
                "BOOK18 23:1",
                "BOOK18 23:2",
                "BOOK18 23:3",
            ]
        )
        results1 = VerseSet.objects.all().search([LANG.EN], "Psalm 23:1-3", default_language_code="tr")
        assert set(results1) == {vs1}

    def test_search_no_query(self):
        # Any language
        vs1 = VerseSet.objects.create(
            name="Psalm 23:1-2",
            slug="psalm-23",
            public=True,
            language_code="en",
            set_type=VerseSetType.PASSAGE,
            created_by=self.account,
        )
        vs1.set_verse_choices(
            [
                "BOOK18 23:1",
                "BOOK18 23:2",
            ]
        )

        # Turkish
        vs2 = VerseSet.objects.create(
            name="Sevdiğim",
            slug="servdigim",
            public=True,
            language_code="tr",
            set_type=VerseSetType.SELECTION,
            created_by=self.account,
        )
        vs2.set_verse_choices(
            [
                "BOOK18 23:1",
            ]
        )

        # English
        vs3 = VerseSet.objects.create(
            name="Faves",
            slug="faves",
            public=True,
            language_code="en",
            set_type=VerseSetType.SELECTION,
            created_by=self.account,
        )
        vs3.set_verse_choices(
            [
                "BOOK18 23:1",
            ]
        )

        # Search in Turkish:
        results = VerseSet.objects.all().search([LANG.TR], "", default_language_code="tr")
        assert set(results) == {vs1, vs2}


class QuickFindTests(SearchTestsMixin, TestBase):
    """
    Test for verse search / quick find functionality
    """

    def test_quick_find_text(self):
        version = self.KJV
        results, more = quick_find("beginning created", version=version)
        assert results[0].verses[0].localized_reference == "Genesis 1:1"

    def test_quick_find_text_turkish(self):
        version = self.TCL02
        # Testing for handling accents and stemming correctly.
        # 'siniz' should be dropped, and word with 'iz' ending
        # should be found.
        results, more = quick_find("övünebilirsiniz", version=version)
        assert results[0].verses[0].localized_reference == "Romalılar 3:27"
        assert "övünebiliriz" in results[0].text

    def test_quick_find_escape(self):
        version = self.KJV
        results, more = quick_find("beginning & | created", version=version)
        assert results[0].verses[0].localized_reference == "Genesis 1:1"
        results, more = quick_find("Genesissss 1:1", version=version)
        assert len(results) == 0
        results, more = quick_find("Hello!", version=version)
        assert len(results) == 0

    def test_quick_find_song_of_solomon(self):
        version = self.KJV
        results, more = quick_find("Song of Solomon 1:1", version)
        assert results[0].verses[0].localized_reference == "Song of Solomon 1:1"

    def test_quick_find_numbered_book(self):
        version = self.KJV
        results, more = quick_find("1 Corinthians 1:3", version=version)
        assert results[0].verses[0].localized_reference == "1 Corinthians 1:3"

    def test_quick_find_book_names_as_searches(self):
        # Need to be able to find words that happen to be in the names of books.
        version = self.NET
        results, more = quick_find("James", version, allow_searches=True)
        assert len(results) == 1
        assert results[0].verses[0].localized_reference == "Matthew 4:21"

    def test_quick_find_passage_mode(self):
        version = self.KJV
        results, more = quick_find("Genesis 1:1-2:2", version, allow_searches=False, max_length=1000)
        assert results is not None

    def test_quick_find_merged_verse(self):
        version = self.TCL02
        # There is no 3:25, 3:26 - rather there is 3:25-26
        refs = [
            ("Romalılar 3:25", "Romalılar 3:25-26", 25, 26, 1, 1),
            ("Romalılar 3:26", "Romalılar 3:25-26", 25, 26, 1, 1),
            ("Romalılar 3:25-26", "Romalılar 3:25-26", 25, 26, 1, 2),
            ("Romalılar 3:24-25", "Romalılar 3:24-26", 24, 26, 2, 2),
            ("Romalılar 3:26-27", "Romalılar 3:25-27", 25, 27, 2, 2),
        ]
        for ref, corrected_ref, start_verse, end_verse, length, q in refs:
            with self.assertNumQueries(q):
                with override("en"):
                    results, more = quick_find(ref, version)
                v = results[0]
                # v is always a VerseSearchResult for quick_find results
                assert v.localized_reference == corrected_ref, "For ref " + ref
                assert len(v.verses) == length, "For ref " + ref
                if length == 1:
                    assert v.verses[0].localized_reference == corrected_ref, "For ref " + ref

                # Some tests for parsed_ref attribute that is used by
                # front end
                assert v.parsed_ref.start_verse == start_verse, "For ref " + ref
                assert v.parsed_ref.end_verse == end_verse, "For ref " + ref

    def test_quick_find_special_symbols(self):
        # Testing for crashers due to syntax issues
        quick_find("x (", self.NET)
        quick_find("x &", self.NET)


def test_search_conf():
    for lang in LANGUAGES:
        assert lang.code in POSTGRES_SEARCH_CONFIGURATIONS, f"{lang.code} needs POSTGRES_SEARCH_CONFIGURATIONS defining"
