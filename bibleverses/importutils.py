# Utility functions for importing Bible texts
from collections.abc import Generator

from bibleverses.constants import _BIBLE_BOOKS_FOR_LANG, BIBLE_BOOK_INFO
from bibleverses.languages import LANG
from bibleverses.models import Verse
from bibleverses.parsing import ParsedReference


def create_verse_for_parsed_ref(
    version,
    parsed_ref: ParsedReference,
    text,
    bible_verse_number,
    gapless_bible_verse_number,
    *,
    replacement_verse=None,
    updated_verse=None,
    missing=False,
) -> Verse:
    return version.verse_set.create(
        localized_reference=parsed_ref.canonical_form(),
        text_saved=text,
        book_number=parsed_ref.book_number,
        chapter_number=parsed_ref.start_chapter,
        first_verse_number=parsed_ref.start_verse,
        last_verse_number=parsed_ref.end_verse,
        bible_verse_number=bible_verse_number,
        gapless_bible_verse_number=gapless_bible_verse_number,
        missing=missing,
        replacement_verse=replacement_verse,
        updated_verse=updated_verse,
    )


def get_all_parsed_refs(lang=LANG.INTERNAL) -> Generator[ParsedReference, None, None]:
    for book_num, book_name in enumerate(_BIBLE_BOOKS_FOR_LANG[lang]):
        info = BIBLE_BOOK_INFO[f"BOOK{book_num}"]
        for chapter in range(1, info.chapter_count + 1):
            for verse in range(1, info.verse_counts[chapter] + 1):
                yield ParsedReference(language_code=lang, book_name=book_name, start_chapter=chapter, start_verse=verse)


def parsed_ref_to_pysword_args(ref: ParsedReference):
    """
    Given ParsedRef, returns args suitable for passing to PySword Bible.get method
    """
    assert ref.end_chapter == ref.start_chapter and ref.end_verse == ref.start_verse
    book_name = ref.translate_to(LANG.EN).book_name
    # Adjust book names
    book_name = (
        book_name.replace("1 ", "I ")
        .replace("2 ", "II ")
        .replace("3 ", "III ")
        .replace("Psalm", "Psalms")
        .replace("Revelation", "Revelation of John")
    )
    return dict(books=[book_name], chapters=[ref.start_chapter], verses=[ref.start_verse])
