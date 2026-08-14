from .constants import (
    _BIBLE_BOOK_ALTERNATIVES_FOR_LANG,
    _BIBLE_BOOK_NUMBERS_FOR_LANG,
    _BIBLE_BOOKS_FOR_LANG,
    _SINGLE_CHAPTER_BOOK_NUMBERS,
    BIBLE_BOOK_COUNT,
)

__all__ = [
    "get_bible_books",
    "get_bible_book_abbreviation_map",
    "get_bible_book_number",
    "get_bible_book_name",
    "is_single_chapter_book",
    "BIBLE_BOOK_COUNT",
]


def get_bible_books(language_code):
    """
    For a given language code, returns the list of Bible books (in normal order)
    """
    return _BIBLE_BOOKS_FOR_LANG[language_code]


def get_bible_book_abbreviation_map(language_code):
    """
    For a given language code, returns the mapping
    of all acceptable book names to the canonical name
    """
    return _BIBLE_BOOK_ALTERNATIVES_FOR_LANG[language_code]


def get_bible_book_number(language_code, book_name):
    """
    For a given language code and localized book name,
    returns the 0-based index of that book.
    """
    return _BIBLE_BOOK_NUMBERS_FOR_LANG[language_code][book_name]


def get_bible_book_name(language_code, number):
    """
    For a given language code and 0-based index of a book number,
    returns the book name.
    """
    return _BIBLE_BOOKS_FOR_LANG[language_code][number]


def is_single_chapter_book(book_number):
    return book_number in _SINGLE_CHAPTER_BOOK_NUMBERS
