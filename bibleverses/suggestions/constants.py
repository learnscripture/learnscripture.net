# -- Bible handling

from bibleverses.books import get_bible_book_name, get_bible_book_number
from bibleverses.languages import LANG


def english_book_name_to_internal(book_name: str) -> str:
    return get_bible_book_name(LANG.INTERNAL, get_bible_book_number(LANG.EN, book_name))


def internal_book_name_to_lang(book_name: str, language_code: str):
    return get_bible_book_name(language_code, get_bible_book_number(LANG.INTERNAL, book_name))


def english_book_name_to_internal_l(book_list: list[str]) -> list[str]:
    return list(map(english_book_name_to_internal, book_list))


TORAH = english_book_name_to_internal_l(["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"])

HISTORY = english_book_name_to_internal_l(
    [
        "Joshua",
        "Judges",
        "Ruth",
        "1 Samuel",
        "2 Samuel",
        "1 Kings",
        "2 Kings",
        "1 Chronicles",
        "2 Chronicles",
        "Ezra",
        "Nehemiah",
        "Esther",
    ]
)

WISDOM = english_book_name_to_internal_l(["Job", "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon"])

PROPHETS = english_book_name_to_internal_l(
    [
        "Isaiah",
        "Jeremiah",
        "Lamentations",
        "Ezekiel",
        "Daniel",
        "Hosea",
        "Joel",
        "Amos",
        "Obadiah",
        "Jonah",
        "Micah",
        "Nahum",
        "Habakkuk",
        "Zephaniah",
        "Haggai",
        "Zechariah",
        "Malachi",
    ]
)

NT_HISTORY = english_book_name_to_internal_l(["Matthew", "Mark", "Luke", "John", "Acts"])

EPISTLES = english_book_name_to_internal_l(
    [
        "Romans",
        "1 Corinthians",
        "2 Corinthians",
        "Galatians",
        "Ephesians",
        "Philippians",
        "Colossians",
        "1 Thessalonians",
        "2 Thessalonians",
        "1 Timothy",
        "2 Timothy",
        "Titus",
        "Philemon",
        "Hebrews",
        "James",
        "1 Peter",
        "2 Peter",
        "1 John",
        "2 John",
        "3 John",
        "Jude",
        "Revelation",
    ]
)

BIBLE_BOOK_GROUPS = [TORAH, HISTORY, WISDOM, PROPHETS, NT_HISTORY, EPISTLES]


def get_bible_book_groups(language_code: str) -> list[list[str]]:
    return [[internal_book_name_to_lang(b, language_code) for b in group] for group in BIBLE_BOOK_GROUPS]


def similar_books(book_name: str, language_code: str):
    """
    Return a list of similar Bible books to the passed in book name
    """
    retval = []
    for g in get_bible_book_groups(language_code):
        if book_name in g:
            retval.extend(g)
    if book_name not in retval:
        retval.append(book_name)
    return retval


# -- Other misc

MIN_SUGGESTIONS = 20
MAX_SUGGESTIONS = 40


# -- Analysis
WORD_COUNTS_ANALYSIS = "WORD_COUNTS_ANALYSIS"
FIRST_WORD_FREQUENCY_ANALYSIS = "FIRST_WORD_FREQUENCY_ANALYSIS"
THESAURUS_ANALYSIS = "THESAURUS_ANALYSIS"
MARKOV_1_ANALYSIS = "MARKOV_1_ANALYSIS"
MARKOV_2_ANALYSIS = "MARKOV_2_ANALYSIS"
MARKOV_3_ANALYSIS = "MARKOV_3_ANALYSIS"


def markov_analysis_name_for_size(size):
    return {1: MARKOV_1_ANALYSIS, 2: MARKOV_2_ANALYSIS, 3: MARKOV_3_ANALYSIS}[size]


# Key to indicate the whole of a text is to be used
ALL_TEXT = "all"
