import pytest
from django_ftl import override

from bibleverses.books import get_bible_book_number, get_bible_books, is_single_chapter_book
from bibleverses.languages import LANG, LANGUAGES, normalize_reference_input_turkish
from bibleverses.models import InvalidVerseReference
from bibleverses.parsing import (
    ParsedReference,
    parse_unvalidated_localized_reference,
    parse_validated_localized_reference,
)


def pv(lang, ref):
    """
    parse_validated_localized_reference, with extra checks.
    """
    retval = parse_validated_localized_reference(lang, ref)
    assert retval.canonical_form() == ref
    return retval


def pu(lang, query, **kwargs):
    """
    parse_unvalidated_localized_reference
    """
    return parse_unvalidated_localized_reference(lang, query, **kwargs)


def test_unparsable_strict():
    with pytest.raises(InvalidVerseReference):
        pv(LANG.EN, "Garbage")
    with pytest.raises(InvalidVerseReference):
        pv(LANG.EN, "Genesis 1:x")


def test_unparsable_loose():
    assert pu(LANG.EN, "Garbage") is None
    assert pu(LANG.EN, "Genesis 1:x") is None


def test_bad_order_strict():
    with override("en"):
        with pytest.raises(InvalidVerseReference):
            pv(LANG.EN, "Genesis 1:3-2")
        with pytest.raises(InvalidVerseReference):
            pv(LANG.EN, "Genesis 2:1-1:10")


def test_bad_order_loose():
    with override("en"):
        with pytest.raises(InvalidVerseReference):
            pu(LANG.EN, "genesis 1:3-2")
        with pytest.raises(InvalidVerseReference):
            pu(LANG.EN, "genesis 2:1 - 1:10")


def test_book():
    parsed = pv(LANG.EN, "Genesis 1")
    assert parsed.book_number == 0
    assert parsed.book_name == "Genesis"
    assert parsed.start_chapter == 1
    assert parsed.end_chapter == 1
    assert parsed.start_verse is None
    assert parsed.end_verse is None
    assert not parsed.is_single_verse()
    assert not parsed.is_whole_book()
    assert parsed.is_whole_chapter()


def test_single_verse_strict():
    parsed = pv(LANG.EN, "Genesis 1:1")
    _test_single_verse(parsed)


def test_single_verse_loose():
    parsed = pu(LANG.EN, "Gen 1 v 1")
    _test_single_verse(parsed)


def _test_single_verse(parsed):
    assert parsed.book_number == 0
    assert parsed.book_name == "Genesis"
    assert parsed.start_chapter == 1
    assert parsed.end_chapter == 1
    assert parsed.start_verse == 1
    assert parsed.end_verse == 1
    assert parsed.is_single_verse()
    assert not parsed.is_whole_book()
    assert not parsed.is_whole_chapter()
    assert parsed.get_start() == parsed
    assert parsed.get_end() == parsed


def test_verse_range_strict():
    parsed = pv(LANG.EN, "Genesis 1:1-2")
    _test_verse_range(parsed)


def test_verse_range_loose():
    parsed = pu(LANG.EN, "gen 1 v 1 - 2")
    _test_verse_range(parsed)

    parsed = pu(LANG.EN, "Gen 1:1\u20132")
    _test_verse_range(parsed)


def _test_verse_range(parsed):
    assert parsed.book_number == 0
    assert parsed.book_name == "Genesis"
    assert parsed.start_chapter == 1
    assert parsed.end_chapter == 1
    assert parsed.start_verse == 1
    assert parsed.end_verse == 2
    assert not parsed.is_single_verse()
    assert not parsed.is_whole_book()
    assert not parsed.is_whole_chapter()

    start = parsed.get_start()
    assert start.start_chapter == 1
    assert start.end_chapter == 1
    assert start.start_verse == 1
    assert start.end_verse == 1

    end = parsed.get_end()
    assert end.start_chapter == 1
    assert end.end_chapter == 1
    assert end.start_verse == 2
    assert end.end_verse == 2


def test_verse_range_2_strict():
    parsed = pv(LANG.EN, "Genesis 1:2-3:4")
    _test_verse_range_2(parsed)


def test_verse_range_2_loose():
    parsed = pu(LANG.EN, "gen 1v2 - 3v4")
    _test_verse_range_2(parsed)


def _test_verse_range_2(parsed):
    assert parsed.start_chapter == 1
    assert parsed.end_chapter == 3
    assert parsed.start_verse == 2
    assert parsed.end_verse == 4
    assert not parsed.is_single_verse()
    assert not parsed.is_whole_book()
    assert not parsed.is_whole_chapter()

    start = parsed.get_start()
    assert start.start_chapter == 1
    assert start.end_chapter == 1
    assert start.start_verse == 2
    assert start.end_verse == 2

    end = parsed.get_end()
    assert end.start_chapter == 3
    assert end.end_chapter == 3
    assert end.start_verse == 4
    assert end.end_verse == 4


def test_from_start_and_end():
    parsed = pv(LANG.EN, "Genesis 1:2-3:4")
    combined = ParsedReference.from_start_and_end(parsed.get_start(), parsed.get_end())
    assert parsed == combined

    parsed2 = pv(LANG.EN, "Genesis 1:1")
    combined2 = ParsedReference.from_start_and_end(parsed2.get_start(), parsed2.get_end())
    assert parsed2 == combined2

    parsed3 = pv(LANG.EN, "Genesis 1")
    combined3 = ParsedReference.from_start_and_end(parsed3.get_start(), parsed3.get_end())
    assert parsed3 == combined3


TESTDATA_PARSE_BOOKS = [(lang, book) for lang in LANGUAGES for book in get_bible_books(lang.code)]


@pytest.mark.parametrize("lang,book", TESTDATA_PARSE_BOOKS)
def test_parse_books(lang, book):
    # Check that the book names parse back to themselves.
    r = pu(lang.code, book, allow_whole_book=True).canonical_form()
    book_number = get_bible_book_number(lang.code, book)
    if is_single_chapter_book(book_number):
        assert r == book + " 1"
    else:
        assert r == book


def test_single_chapter_books():
    parsed = pu(LANG.EN, "Jude")
    assert parsed.canonical_form() == "Jude 1"
    assert parsed.is_whole_book()
    assert parsed.is_whole_chapter()


def test_constraints():
    assert pu(LANG.EN, "Matt 1", allow_whole_book=False, allow_whole_chapter=True).canonical_form() == "Matthew 1"
    assert pu(LANG.EN, "Matt 1", allow_whole_book=False, allow_whole_chapter=False) is None
    assert pu(LANG.EN, "Matt", allow_whole_book=True, allow_whole_chapter=True).canonical_form() == "Matthew"
    assert pu(LANG.EN, "Matt", allow_whole_book=False, allow_whole_chapter=True) is None
    assert pu(LANG.EN, "Jude", allow_whole_book=False, allow_whole_chapter=True).canonical_form() == "Jude 1"


def test_invalid_references():
    with override("en"):
        with pytest.raises(InvalidVerseReference):
            pv(LANG.EN, "Matthew 2:1-1:2")
        # Even with loose parsing, we still propagage InvalidVerseReference, so
        # that the front end code (e.g. quick_find) can recognise that the user
        # tried to enter a verse reference.
        with pytest.raises(InvalidVerseReference):
            pu(LANG.EN, "Matthew 2:1-1:2")


@pytest.mark.parametrize(
    "input_ref,output_ref",
    [
        # Different numbering styles for book names:
        ("1. Timoteos 3:16", "1. Timoteos 3:16"),
        ("1 Timoteos 3:16", "1. Timoteos 3:16"),
        ("1Timoteos 3:16", "1. Timoteos 3:16"),
        ("1tim 3.16", "1. Timoteos 3:16"),
        # Apostrophes optional
        ("Yasanın Tekrarı 1", "Yasa'nın Tekrarı 1"),
        # Turkish people often miss out accents or use the wrong kind of 'i'
        # etc. when typing, especially as keyboards may not support correct
        # characters.
        ("YARATILIS 2:3", "Yaratılış 2:3"),
        ("YARATİLİS 2:3", "Yaratılış 2:3"),
        ("yaratilis 2:3", "Yaratılış 2:3"),
        ("colde sayim 4:5", "Çölde Sayım 4:5"),
        ("EYÜP 1", "Eyüp 1"),
    ],
)
def test_turkish_reference_parsing(input_ref, output_ref):
    assert pu(LANG.TR, input_ref).canonical_form() == output_ref, f"Failure parsing '{input_ref}'"


def test_turkish_reference_normalization():
    assert normalize_reference_input_turkish("  ÂâİIiıÇçŞşÖöÜüĞğ  ") == "aaiiiiccssoouugg"


@pytest.mark.parametrize(
    "input_ref,output_ref",
    [
        # Different numbering styles for book names:
        ("Openbaringen 1:1", "Openbaring 1:1"),
        ("Openb. 1:1", "Openbaring 1:1"),
        ("openb 1:1", "Openbaring 1:1"),
        ("2 Timótheüs 1:3", "2 Timotheüs 1:3"),
        ("2 Timoteüs 1:3", "2 Timotheüs 1:3"),
        ("2 Timoteus 1:3", "2 Timotheüs 1:3"),
    ],
)
def test_dutch_reference_parsing(input_ref, output_ref):
    assert pu(LANG.NL, input_ref).canonical_form() == output_ref, f"Failure parsing '{input_ref}'"


def test_dutch_reference_normalization():
    assert normalize_reference_input_turkish("  ÉüéÜ  ") == "eueu"


def test_to_list():
    def assertListEqual(ref, ref_list):
        parsed_ref = pv("en", ref)
        assert parsed_ref.to_list() == [pv("en", r) for r in ref_list]

    assertListEqual("Genesis 1:1", ["Genesis 1:1"])
    assertListEqual("Genesis 1:1-2", ["Genesis 1:1", "Genesis 1:2"])
    assertListEqual(
        "Genesis 1:30-2:2",
        [
            "Genesis 1:30",
            "Genesis 1:31",
            "Genesis 2:1",
            "Genesis 2:2",
        ],
    )
    assertListEqual(
        "Genesis 1:30-31",
        [
            "Genesis 1:30",
            "Genesis 1:31",
        ],
    )
    assertListEqual(
        "Psalm 23",
        [
            "Psalm 23:1",
            "Psalm 23:2",
            "Psalm 23:3",
            "Psalm 23:4",
            "Psalm 23:5",
            "Psalm 23:6",
        ],
    )
    assertListEqual(
        "Jude 1:25",
        [
            "Jude 1:25",
        ],
    )


def test_get_start_and_get_end():
    assert pv("en", "Genesis 1:1-2").get_start().canonical_form() == "Genesis 1:1"
    assert pv("en", "Genesis 1:1-2").get_end().canonical_form() == "Genesis 1:2"

    assert pv("en", "Genesis 1").get_start().canonical_form() == "Genesis 1:1"
    assert pv("en", "Genesis 1").get_end().canonical_form() == "Genesis 1:31"

    assert pv("en", "Genesis 1:5-3:10").get_start().canonical_form() == "Genesis 1:5"
    assert pv("en", "Genesis 1:5-3:10").get_end().canonical_form() == "Genesis 3:10"


def test_to_list_whole_book():
    parsed_ref = pv("en", "Genesis")
    refs = [item.canonical_form() for item in parsed_ref.to_list()]
    assert refs[0] == "Genesis 1:1"
    assert refs[1] == "Genesis 1:2"
    assert refs[-1] == "Genesis 50:26"


def test_is_in_bounds():
    good_ref = pu(LANG.EN, "Gen 1:1")
    assert good_ref.is_in_bounds()

    bad_ref_1 = pu(LANG.EN, "Gen 100:1")
    assert not bad_ref_1.is_in_bounds()

    bad_ref_2 = pu(LANG.EN, "Gen 1:100")
    assert not bad_ref_2.is_in_bounds()


def test_is_in_bounds_whole_chapter():
    good_ref = pu(LANG.EN, "Psalm 117")
    assert good_ref.is_in_bounds()


def test_is_in_bounds_chapter_zero():
    assert not pu(LANG.EN, "1 Corinthians 0").is_in_bounds()
    assert not pu(LANG.EN, "1 Corinthians 0:1").is_in_bounds()
    assert not pu(LANG.EN, "1 Corinthians 0:1-0:2").is_in_bounds()
