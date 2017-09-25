from .constants import _BIBLE_BOOK_ABBREVIATIONS_FOR_LANG, _BIBLE_BOOK_NUMBERS_FOR_LANG, _BIBLE_BOOKS_FOR_LANG
from .languages import normalize_search_input


def get_bible_books(language_code):
    """
    For a given language code, returns the list of Bible books (in normal order)
    """
    return _BIBLE_BOOKS_FOR_LANG[language_code]


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


def is_bible_book(language_code, book_name, canonical=False):
    """
    Given a language code and a book name, returns try if the book
    name is a recognized bible book.
    If canonical==True, only the canonical name is accepted,
    otherwise abbreviations etc. are allowed.
    """
    if canonical:
        return book_name in _BIBLE_BOOK_NUMBERS_FOR_LANG[language_code]
    else:
        if is_bible_book(language_code, book_name, canonical=True):
            return True
        else:
            book_name = normalize_search_input(language_code, book_name)
            return book_name in _BIBLE_BOOK_ABBREVIATIONS_FOR_LANG[language_code]


def get_canonical_bible_book_name(language_code, book_name):
    """
    Returns the canonical Bible book name from an abbreviation,
    or raises a LookupError
    """
    if is_bible_book(language_code, book_name, canonical=True):
        return book_name
    return _BIBLE_BOOK_ABBREVIATIONS_FOR_LANG[language_code][normalize_search_input(language_code, book_name)]
