# -*- coding: utf8 -*-
from collections import defaultdict

from .languages import LANGUAGE_CODE_EN, LANGUAGE_CODE_INTERNAL, LANGUAGE_CODE_TR, normalize_reference_input

BIBLE_BOOK_COUNT = 66

# These constants are prefixed _ to indicate private. They are in fact used in
# one other module i.e. books.py, and apart from that should be accessed through
# the utility functions in books.py
_BIBLE_BOOKS_FOR_LANG = {
    LANGUAGE_CODE_EN: ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'],
    LANGUAGE_CODE_TR: ["Yaratılış", "Mısır'dan Çıkış", "Levililer", "Çölde Sayım", "Yasa'nın Tekrarı", "Yeşu", "Hâkimler", "Rut", "1. Samuel", "2. Samuel", "1. Krallar", "2. Krallar", "1. Tarihler", "2. Tarihler", "Ezra", "Nehemya", "Ester", "Eyüp", "Mezmur", "Süleyman'ın Özdeyişleri", "Vaiz", "Ezgiler Ezgisi", "Yeşaya", "Yeremya", "Ağıtlar", "Hezekiel", "Daniel", "Hoşea", "Yoel", "Amos", "Ovadya", "Yunus", "Mika", "Nahum", "Habakkuk", "Sefanya", "Hagay", "Zekeriya", "Malaki", "Matta", "Markos", "Luka", "Yuhanna", "Elçilerin İşleri", "Romalılar", "1. Korintliler", "2. Korintliler", "Galatyalılar", "Efesliler", "Filipililer", "Koloseliler", "1. Selanikliler", "2. Selanikliler", "1. Timoteos", "2. Timoteos", "Titus", "Filimon", "İbraniler", "Yakup", "1. Petrus", "2. Petrus", "1. Yuhanna", "2. Yuhanna", "3. Yuhanna", "Yahuda", "Vahiy"],
    LANGUAGE_CODE_INTERNAL: ["BOOK" + str(i) for i in range(0, BIBLE_BOOK_COUNT)],
}

# Book numbers of books that have a single chapter.
_SINGLE_CHAPTER_BOOK_NUMBERS = [
    _BIBLE_BOOKS_FOR_LANG[LANGUAGE_CODE_EN].index(b)
    for b in ["Obadiah", "Philemon", "2 John", "3 John", "Jude"]
]

_BIBLE_BOOK_NUMBERS_FOR_LANG = {
    lang: dict((n, i) for (i, n) in enumerate(books))
    for lang, books in _BIBLE_BOOKS_FOR_LANG.items()
}


# All possible bible book names, normalized (lower case plus other transformations),
# matched to canonical name:
_BIBLE_BOOK_ABBREVIATIONS_FOR_LANG = {}


def make_bible_book_abbreviations():
    for lang in _BIBLE_BOOKS_FOR_LANG:
        make_bible_book_abbreviations_for_lang(lang)
    make_bible_book_special_cases()


def make_bible_book_abbreviations_for_lang(language_code):
    global _BIBLE_BOOK_ABBREVIATIONS_FOR_LANG
    bible_books = _BIBLE_BOOKS_FOR_LANG[language_code]
    abbreviations = {}
    _BIBLE_BOOK_ABBREVIATIONS_FOR_LANG[language_code] = abbreviations

    nums = {
        LANGUAGE_CODE_EN: {
            '1 ': ['1', 'I ', 'I'],
            '2 ': ['2', 'II ', 'II'],
            '3 ': ['3', 'III ', 'III']
        },
        LANGUAGE_CODE_TR: {
            '1. ': ['1', '1 ', '1.'],
            '2. ': ['2', '2 ', '2.'],
            '3. ': ['3', '3 ', '3.'],
        },
        LANGUAGE_CODE_INTERNAL: {},
    }

    def get_abbrevs(book_name, min_length=2):
        # Get alternatives like '1Peter', 'I Peter' etc.
        # and '1 Pe', '1Pet' etc.
        has_number_prefix = False
        for k, v in nums[language_code].items():
            if book_name.startswith(k):
                has_number_prefix = True
                for prefix in v + [k]:
                    book_stem = book_name[len(k):]
                    for i in range(2, len(book_stem) + 1):
                        yield prefix + book_stem[0:i]

        # Or just alternatives like: 'Ro', 'Rom', .. 'Romans'
        if not has_number_prefix:
            # TODO - this generates silly things sometimes e.g "song o" and "song of
            # s" which no-one would ever write, but they might write it when
            # searching for contents
            for i in range(min_length, len(book_name) + 1):
                yield book_name[0:i]

    # Get all abbreviations
    d = {}
    for b in bible_books:
        d[b] = [normalize_reference_input(language_code, i) for i in get_abbrevs(b)]

    # Now need to make unique. Create a reverse dictionary.
    d2 = defaultdict(set)
    for book_name, abbrev_list in d.items():
        for abbrev in abbrev_list:
            d2[abbrev].add(book_name)

    # Now, if any value in d2 has more than one item,
    # it is ambiguous and should be removed altogether,
    # otherwise replaced with the single value.
    d3 = {}
    for abbrev, book_names in d2.items():
        if len(book_names) == 1:
            d3[abbrev] = book_names.pop()

    abbreviations.update(d3)


def make_bible_book_special_cases():
    # Some special cases that don't fit above pattern
    _BIBLE_BOOK_ABBREVIATIONS_FOR_LANG[LANGUAGE_CODE_EN].update({
        'dt': 'Deuteronomy',
        'gn': 'Genesis',
        'hg': 'Haggai',
        'jb': 'Job',
        'jl': 'Joel',
        'jgs': 'Judges',
        'jdg': 'Judges',
        'jas': 'James',
        'jm': 'James',
        'jn': 'John',
        'jnh': 'Jonah',
        'jsh': 'Joshua',
        'jud': 'Jude',
        'lev': 'Leviticus',
        'mk': 'Mark',
        'mrk': 'Mark',
        'mt': 'Matthew',
        'nm': 'Numbers',
        'prv': 'Proverbs',
        'phm': 'Philemon',
        'phil': 'Philippians',
        'php': 'Philippians',
        'psalms': 'Psalm',
        'rm': 'Romans',
        'sg': 'Song of Solomon',
        'sng': 'Song of Solomon',
    })

    # TODO - anything else for Turkish?
    _BIBLE_BOOK_ABBREVIATIONS_FOR_LANG[LANGUAGE_CODE_TR].update({
        'mezmurlar': 'Mezmur',
        'mz': 'Mezmur',
    })


def checks():
    for lang, books in _BIBLE_BOOKS_FOR_LANG.items():
        if len(books) != BIBLE_BOOK_COUNT:
            raise AssertionError("Language {0} doesn't have the expected number of Bible books defined!".format(lang))


make_bible_book_abbreviations()
checks()
