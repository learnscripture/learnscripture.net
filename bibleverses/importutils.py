# Utility functions for importing Bible texts


def create_verse_for_parsed_ref(
    version,
    parsed_ref,
    text,
    bible_verse_number,
    gapless_bible_verse_number,
    *,
    replacement_verse=None,
    updated_verse=None,
    missing=False,
):
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
