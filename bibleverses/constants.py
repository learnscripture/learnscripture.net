# See also bible_book_info.ts

import parsy as P

from .languages import LANG, normalize_reference_input

BIBLE_BOOK_COUNT = 66

# These constants are prefixed _ to indicate private. They are in fact used in
# one other module i.e. books.py, and apart from that should be accessed through
# the utility functions in books.py
_BIBLE_BOOKS_FOR_LANG = {
    LANG.EN: [
        "Genesis",
        "Exodus",
        "Leviticus",
        "Numbers",
        "Deuteronomy",
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
        "Job",
        "Psalm",
        "Proverbs",
        "Ecclesiastes",
        "Song of Solomon",
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
        "Matthew",
        "Mark",
        "Luke",
        "John",
        "Acts",
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
    ],
    LANG.NL: [
        "Genesis",
        "Exodus",
        "Leviticus",
        "Numeri",
        "Deuteronomium",
        "Jozua",
        "Richteren",
        "Ruth",
        "1 Samuël",
        "2 Samuël",
        "1 Koningen",
        "2 Koningen",
        "1 Kronieken",
        "2 Kronieken",
        "Ezra",
        "Nehemia",
        "Esther",
        "Job",
        "Psalm",
        "Spreuken",
        "Prediker",
        "Hooglied",
        "Jesaja",
        "Jeremia",
        "Klaagliederen",
        "Ezechiël",
        "Daniël",
        "Hosea",
        "Joël",
        "Amos",
        "Obadja",
        "Jona",
        "Micha",
        "Nahum",
        "Habakuk",
        "Zefanja",
        "Haggaï",
        "Zacharia",
        "Maleachi",
        "Mattheüs",
        "Markus",
        "Lukas",
        "Johannes",
        "Handelingen",
        "Romeinen",
        "1 Korinthe",
        "2 Korinthe",
        "Galaten",
        "Efeze",
        "Filippenzen",
        "Kolossenzen",
        "1 Thessalonicenzen",
        "2 Thessalonicenzen",
        "1 Timotheüs",
        "2 Timotheüs",
        "Titus",
        "Filemon",
        "Hebreeën",
        "Jakobus",
        "1 Petrus",
        "2 Petrus",
        "1 Johannes",
        "2 Johannes",
        "3 Johannes",
        "Judas",
        "Openbaring",
    ],
    LANG.TR: [
        "Yaratılış",
        "Mısır'dan Çıkış",
        "Levililer",
        "Çölde Sayım",
        "Yasa'nın Tekrarı",
        "Yeşu",
        "Hâkimler",
        "Rut",
        "1. Samuel",
        "2. Samuel",
        "1. Krallar",
        "2. Krallar",
        "1. Tarihler",
        "2. Tarihler",
        "Ezra",
        "Nehemya",
        "Ester",
        "Eyüp",
        "Mezmurlar",
        "Süleyman'ın Özdeyişleri",
        "Vaiz",
        "Ezgiler Ezgisi",
        "Yeşaya",
        "Yeremya",
        "Ağıtlar",
        "Hezekiel",
        "Daniel",
        "Hoşea",
        "Yoel",
        "Amos",
        "Ovadya",
        "Yunus",
        "Mika",
        "Nahum",
        "Habakkuk",
        "Sefanya",
        "Hagay",
        "Zekeriya",
        "Malaki",
        "Matta",
        "Markos",
        "Luka",
        "Yuhanna",
        "Elçilerin İşleri",
        "Romalılar",
        "1. Korintliler",
        "2. Korintliler",
        "Galatyalılar",
        "Efesliler",
        "Filipililer",
        "Koloseliler",
        "1. Selanikliler",
        "2. Selanikliler",
        "1. Timoteos",
        "2. Timoteos",
        "Titus",
        "Filimon",
        "İbraniler",
        "Yakup",
        "1. Petrus",
        "2. Petrus",
        "1. Yuhanna",
        "2. Yuhanna",
        "3. Yuhanna",
        "Yahuda",
        "Vahiy",
    ],
    LANG.ES: [
        "Génesis",
        "Éxodo",
        "Levítico",
        "Números",
        "Deuteronomio",
        "Josué",
        "Jueces",
        "Rut",
        "1 Samuel",
        "2 Samuel",
        "1 Reyes",
        "2 Reyes",
        "1 Crónicas",
        "2 Crónicas",
        "Esdras",
        "Nehemías",
        "Ester",
        "Job",
        "Salmos",
        "Proverbios",
        "Eclesiastés",
        "El Cantar de los Cantares",
        "Isaías",
        "Jeremías",
        "Lamentaciones",
        "Ezequiel",
        "Daniel",
        "Oseas",
        "Joel",
        "Amós",
        "Abdías",
        "Jonás",
        "Miqueas",
        "Nahúm",
        "Habacuc",
        "Sofonías",
        "Hageo",
        "Zacarías",
        "Malaquías",
        "Mateo",
        "Marcos",
        "Lucas",
        "Juan",
        "Hechos",
        "Romanos",
        "1 Corintios",
        "2 Corintios",
        "Gálatas",
        "Efesios",
        "Filipenses",
        "Colosenses",
        "1 Tesalonicenses",
        "2 Tesalonicenses",
        "1 Timoteo",
        "2 Timoteo",
        "Tito",
        "Filemón",
        "Hebreos",
        "Santiago",
        "1 Pedro",
        "2 Pedro",
        "1 Juan",
        "2 Juan",
        "3 Juan",
        "Judas",
        "Apocalipsis"
    ],
    LANG.INTERNAL: ["BOOK" + str(i) for i in range(0, BIBLE_BOOK_COUNT)],
}

# Book numbers of books that have a single chapter.
_SINGLE_CHAPTER_BOOK_NUMBERS = [
    _BIBLE_BOOKS_FOR_LANG[LANG.EN].index(b) for b in ["Obadiah", "Philemon", "2 John", "3 John", "Jude"]
]

_BIBLE_BOOK_NUMBERS_FOR_LANG = {
    lang: {n: i for (i, n) in enumerate(books)} for lang, books in _BIBLE_BOOKS_FOR_LANG.items()
}


BIBLE_BOOK_INFO = dict(
    [
        (
            "BOOK0",
            {
                "chapter_count": 50,
                "verse_counts": {
                    1: 31,
                    2: 25,
                    3: 24,
                    4: 26,
                    5: 32,
                    6: 22,
                    7: 24,
                    8: 22,
                    9: 29,
                    10: 32,
                    11: 32,
                    12: 20,
                    13: 18,
                    14: 24,
                    15: 21,
                    16: 16,
                    17: 27,
                    18: 33,
                    19: 38,
                    20: 18,
                    21: 34,
                    22: 24,
                    23: 20,
                    24: 67,
                    25: 34,
                    26: 35,
                    27: 46,
                    28: 22,
                    29: 35,
                    30: 43,
                    31: 55,
                    32: 32,
                    33: 20,
                    34: 31,
                    35: 29,
                    36: 43,
                    37: 36,
                    38: 30,
                    39: 23,
                    40: 23,
                    41: 57,
                    42: 38,
                    43: 34,
                    44: 34,
                    45: 28,
                    46: 34,
                    47: 31,
                    48: 22,
                    49: 33,
                    50: 26,
                },
            },
        ),
        (
            "BOOK1",
            {
                "chapter_count": 40,
                "verse_counts": {
                    1: 22,
                    2: 25,
                    3: 22,
                    4: 31,
                    5: 23,
                    6: 30,
                    7: 25,
                    8: 32,
                    9: 35,
                    10: 29,
                    11: 10,
                    12: 51,
                    13: 22,
                    14: 31,
                    15: 27,
                    16: 36,
                    17: 16,
                    18: 27,
                    19: 25,
                    20: 26,
                    21: 36,
                    22: 31,
                    23: 33,
                    24: 18,
                    25: 40,
                    26: 37,
                    27: 21,
                    28: 43,
                    29: 46,
                    30: 38,
                    31: 18,
                    32: 35,
                    33: 23,
                    34: 35,
                    35: 35,
                    36: 38,
                    37: 29,
                    38: 31,
                    39: 43,
                    40: 38,
                },
            },
        ),
        (
            "BOOK2",
            {
                "chapter_count": 27,
                "verse_counts": {
                    1: 17,
                    2: 16,
                    3: 17,
                    4: 35,
                    5: 19,
                    6: 30,
                    7: 38,
                    8: 36,
                    9: 24,
                    10: 20,
                    11: 47,
                    12: 8,
                    13: 59,
                    14: 57,
                    15: 33,
                    16: 34,
                    17: 16,
                    18: 30,
                    19: 37,
                    20: 27,
                    21: 24,
                    22: 33,
                    23: 44,
                    24: 23,
                    25: 55,
                    26: 46,
                    27: 34,
                },
            },
        ),
        (
            "BOOK3",
            {
                "chapter_count": 36,
                "verse_counts": {
                    1: 54,
                    2: 34,
                    3: 51,
                    4: 49,
                    5: 31,
                    6: 27,
                    7: 89,
                    8: 26,
                    9: 23,
                    10: 36,
                    11: 35,
                    12: 16,
                    13: 33,
                    14: 45,
                    15: 41,
                    16: 50,
                    17: 13,
                    18: 32,
                    19: 22,
                    20: 29,
                    21: 35,
                    22: 41,
                    23: 30,
                    24: 25,
                    25: 18,
                    26: 65,
                    27: 23,
                    28: 31,
                    29: 40,
                    30: 16,
                    31: 54,
                    32: 42,
                    33: 56,
                    34: 29,
                    35: 34,
                    36: 13,
                },
            },
        ),
        (
            "BOOK4",
            {
                "chapter_count": 34,
                "verse_counts": {
                    1: 46,
                    2: 37,
                    3: 29,
                    4: 49,
                    5: 33,
                    6: 25,
                    7: 26,
                    8: 20,
                    9: 29,
                    10: 22,
                    11: 32,
                    12: 32,
                    13: 18,
                    14: 29,
                    15: 23,
                    16: 22,
                    17: 20,
                    18: 22,
                    19: 21,
                    20: 20,
                    21: 23,
                    22: 30,
                    23: 25,
                    24: 22,
                    25: 19,
                    26: 19,
                    27: 26,
                    28: 68,
                    29: 29,
                    30: 20,
                    31: 30,
                    32: 52,
                    33: 29,
                    34: 12,
                },
            },
        ),
        (
            "BOOK5",
            {
                "chapter_count": 24,
                "verse_counts": {
                    1: 18,
                    2: 24,
                    3: 17,
                    4: 24,
                    5: 15,
                    6: 27,
                    7: 26,
                    8: 35,
                    9: 27,
                    10: 43,
                    11: 23,
                    12: 24,
                    13: 33,
                    14: 15,
                    15: 63,
                    16: 10,
                    17: 18,
                    18: 28,
                    19: 51,
                    20: 9,
                    21: 45,
                    22: 34,
                    23: 16,
                    24: 33,
                },
            },
        ),
        (
            "BOOK6",
            {
                "chapter_count": 21,
                "verse_counts": {
                    1: 36,
                    2: 23,
                    3: 31,
                    4: 24,
                    5: 31,
                    6: 40,
                    7: 25,
                    8: 35,
                    9: 57,
                    10: 18,
                    11: 40,
                    12: 15,
                    13: 25,
                    14: 20,
                    15: 20,
                    16: 31,
                    17: 13,
                    18: 31,
                    19: 30,
                    20: 48,
                    21: 25,
                },
            },
        ),
        ("BOOK7", {"chapter_count": 4, "verse_counts": {1: 22, 2: 23, 3: 18, 4: 22}}),
        (
            "BOOK8",
            {
                "chapter_count": 31,
                "verse_counts": {
                    1: 28,
                    2: 36,
                    3: 21,
                    4: 22,
                    5: 12,
                    6: 21,
                    7: 17,
                    8: 22,
                    9: 27,
                    10: 27,
                    11: 15,
                    12: 25,
                    13: 23,
                    14: 52,
                    15: 35,
                    16: 23,
                    17: 58,
                    18: 30,
                    19: 24,
                    20: 42,
                    21: 15,
                    22: 23,
                    23: 29,
                    24: 22,
                    25: 44,
                    26: 25,
                    27: 12,
                    28: 25,
                    29: 11,
                    30: 31,
                    31: 13,
                },
            },
        ),
        (
            "BOOK9",
            {
                "chapter_count": 24,
                "verse_counts": {
                    1: 27,
                    2: 32,
                    3: 39,
                    4: 12,
                    5: 25,
                    6: 23,
                    7: 29,
                    8: 18,
                    9: 13,
                    10: 19,
                    11: 27,
                    12: 31,
                    13: 39,
                    14: 33,
                    15: 37,
                    16: 23,
                    17: 29,
                    18: 33,
                    19: 43,
                    20: 26,
                    21: 22,
                    22: 51,
                    23: 39,
                    24: 25,
                },
            },
        ),
        (
            "BOOK10",
            {
                "chapter_count": 22,
                "verse_counts": {
                    1: 53,
                    2: 46,
                    3: 28,
                    4: 34,
                    5: 18,
                    6: 38,
                    7: 51,
                    8: 66,
                    9: 28,
                    10: 29,
                    11: 43,
                    12: 33,
                    13: 34,
                    14: 31,
                    15: 34,
                    16: 34,
                    17: 24,
                    18: 46,
                    19: 21,
                    20: 43,
                    21: 29,
                    22: 53,
                },
            },
        ),
        (
            "BOOK11",
            {
                "chapter_count": 25,
                "verse_counts": {
                    1: 18,
                    2: 25,
                    3: 27,
                    4: 44,
                    5: 27,
                    6: 33,
                    7: 20,
                    8: 29,
                    9: 37,
                    10: 36,
                    11: 21,
                    12: 21,
                    13: 25,
                    14: 29,
                    15: 38,
                    16: 20,
                    17: 41,
                    18: 37,
                    19: 37,
                    20: 21,
                    21: 26,
                    22: 20,
                    23: 37,
                    24: 20,
                    25: 30,
                },
            },
        ),
        (
            "BOOK12",
            {
                "chapter_count": 29,
                "verse_counts": {
                    1: 54,
                    2: 55,
                    3: 24,
                    4: 43,
                    5: 26,
                    6: 81,
                    7: 40,
                    8: 40,
                    9: 44,
                    10: 14,
                    11: 47,
                    12: 40,
                    13: 14,
                    14: 17,
                    15: 29,
                    16: 43,
                    17: 27,
                    18: 17,
                    19: 19,
                    20: 8,
                    21: 30,
                    22: 19,
                    23: 32,
                    24: 31,
                    25: 31,
                    26: 32,
                    27: 34,
                    28: 21,
                    29: 30,
                },
            },
        ),
        (
            "BOOK13",
            {
                "chapter_count": 36,
                "verse_counts": {
                    1: 17,
                    2: 18,
                    3: 17,
                    4: 22,
                    5: 14,
                    6: 42,
                    7: 22,
                    8: 18,
                    9: 31,
                    10: 19,
                    11: 23,
                    12: 16,
                    13: 22,
                    14: 15,
                    15: 19,
                    16: 14,
                    17: 19,
                    18: 34,
                    19: 11,
                    20: 37,
                    21: 20,
                    22: 12,
                    23: 21,
                    24: 27,
                    25: 28,
                    26: 23,
                    27: 9,
                    28: 27,
                    29: 36,
                    30: 27,
                    31: 21,
                    32: 33,
                    33: 25,
                    34: 33,
                    35: 27,
                    36: 23,
                },
            },
        ),
        (
            "BOOK14",
            {
                "chapter_count": 10,
                "verse_counts": {1: 11, 2: 70, 3: 13, 4: 24, 5: 17, 6: 22, 7: 28, 8: 36, 9: 15, 10: 44},
            },
        ),
        (
            "BOOK15",
            {
                "chapter_count": 13,
                "verse_counts": {
                    1: 11,
                    2: 20,
                    3: 32,
                    4: 23,
                    5: 19,
                    6: 19,
                    7: 73,
                    8: 18,
                    9: 38,
                    10: 39,
                    11: 36,
                    12: 47,
                    13: 31,
                },
            },
        ),
        (
            "BOOK16",
            {
                "chapter_count": 10,
                "verse_counts": {1: 22, 2: 23, 3: 15, 4: 17, 5: 14, 6: 14, 7: 10, 8: 17, 9: 32, 10: 3},
            },
        ),
        (
            "BOOK17",
            {
                "chapter_count": 42,
                "verse_counts": {
                    1: 22,
                    2: 13,
                    3: 26,
                    4: 21,
                    5: 27,
                    6: 30,
                    7: 21,
                    8: 22,
                    9: 35,
                    10: 22,
                    11: 20,
                    12: 25,
                    13: 28,
                    14: 22,
                    15: 35,
                    16: 22,
                    17: 16,
                    18: 21,
                    19: 29,
                    20: 29,
                    21: 34,
                    22: 30,
                    23: 17,
                    24: 25,
                    25: 6,
                    26: 14,
                    27: 23,
                    28: 28,
                    29: 25,
                    30: 31,
                    31: 40,
                    32: 22,
                    33: 33,
                    34: 37,
                    35: 16,
                    36: 33,
                    37: 24,
                    38: 41,
                    39: 30,
                    40: 24,
                    41: 34,
                    42: 17,
                },
            },
        ),
        (
            "BOOK18",
            {
                "chapter_count": 150,
                "verse_counts": {
                    1: 6,
                    2: 12,
                    3: 8,
                    4: 8,
                    5: 12,
                    6: 10,
                    7: 17,
                    8: 9,
                    9: 20,
                    10: 18,
                    11: 7,
                    12: 8,
                    13: 6,
                    14: 7,
                    15: 5,
                    16: 11,
                    17: 15,
                    18: 50,
                    19: 14,
                    20: 9,
                    21: 13,
                    22: 31,
                    23: 6,
                    24: 10,
                    25: 22,
                    26: 12,
                    27: 14,
                    28: 9,
                    29: 11,
                    30: 12,
                    31: 24,
                    32: 11,
                    33: 22,
                    34: 22,
                    35: 28,
                    36: 12,
                    37: 40,
                    38: 22,
                    39: 13,
                    40: 17,
                    41: 13,
                    42: 11,
                    43: 5,
                    44: 26,
                    45: 17,
                    46: 11,
                    47: 9,
                    48: 14,
                    49: 20,
                    50: 23,
                    51: 19,
                    52: 9,
                    53: 6,
                    54: 7,
                    55: 23,
                    56: 13,
                    57: 11,
                    58: 11,
                    59: 17,
                    60: 12,
                    61: 8,
                    62: 12,
                    63: 11,
                    64: 10,
                    65: 13,
                    66: 20,
                    67: 7,
                    68: 35,
                    69: 36,
                    70: 5,
                    71: 24,
                    72: 20,
                    73: 28,
                    74: 23,
                    75: 10,
                    76: 12,
                    77: 20,
                    78: 72,
                    79: 13,
                    80: 19,
                    81: 16,
                    82: 8,
                    83: 18,
                    84: 12,
                    85: 13,
                    86: 17,
                    87: 7,
                    88: 18,
                    89: 52,
                    90: 17,
                    91: 16,
                    92: 15,
                    93: 5,
                    94: 23,
                    95: 11,
                    96: 13,
                    97: 12,
                    98: 9,
                    99: 9,
                    100: 5,
                    101: 8,
                    102: 28,
                    103: 22,
                    104: 35,
                    105: 45,
                    106: 48,
                    107: 43,
                    108: 13,
                    109: 31,
                    110: 7,
                    111: 10,
                    112: 10,
                    113: 9,
                    114: 8,
                    115: 18,
                    116: 19,
                    117: 2,
                    118: 29,
                    119: 176,
                    120: 7,
                    121: 8,
                    122: 9,
                    123: 4,
                    124: 8,
                    125: 5,
                    126: 6,
                    127: 5,
                    128: 6,
                    129: 8,
                    130: 8,
                    131: 3,
                    132: 18,
                    133: 3,
                    134: 3,
                    135: 21,
                    136: 26,
                    137: 9,
                    138: 8,
                    139: 24,
                    140: 13,
                    141: 10,
                    142: 7,
                    143: 12,
                    144: 15,
                    145: 21,
                    146: 10,
                    147: 20,
                    148: 14,
                    149: 9,
                    150: 6,
                },
            },
        ),
        (
            "BOOK19",
            {
                "chapter_count": 31,
                "verse_counts": {
                    1: 33,
                    2: 22,
                    3: 35,
                    4: 27,
                    5: 23,
                    6: 35,
                    7: 27,
                    8: 36,
                    9: 18,
                    10: 32,
                    11: 31,
                    12: 28,
                    13: 25,
                    14: 35,
                    15: 33,
                    16: 33,
                    17: 28,
                    18: 24,
                    19: 29,
                    20: 30,
                    21: 31,
                    22: 29,
                    23: 35,
                    24: 34,
                    25: 28,
                    26: 28,
                    27: 27,
                    28: 28,
                    29: 27,
                    30: 33,
                    31: 31,
                },
            },
        ),
        (
            "BOOK20",
            {
                "chapter_count": 12,
                "verse_counts": {1: 18, 2: 26, 3: 22, 4: 16, 5: 20, 6: 12, 7: 29, 8: 17, 9: 18, 10: 20, 11: 10, 12: 14},
            },
        ),
        ("BOOK21", {"chapter_count": 8, "verse_counts": {1: 17, 2: 17, 3: 11, 4: 16, 5: 16, 6: 13, 7: 13, 8: 14}}),
        (
            "BOOK22",
            {
                "chapter_count": 66,
                "verse_counts": {
                    1: 31,
                    2: 22,
                    3: 26,
                    4: 6,
                    5: 30,
                    6: 13,
                    7: 25,
                    8: 22,
                    9: 21,
                    10: 34,
                    11: 16,
                    12: 6,
                    13: 22,
                    14: 32,
                    15: 9,
                    16: 14,
                    17: 14,
                    18: 7,
                    19: 25,
                    20: 6,
                    21: 17,
                    22: 25,
                    23: 18,
                    24: 23,
                    25: 12,
                    26: 21,
                    27: 13,
                    28: 29,
                    29: 24,
                    30: 33,
                    31: 9,
                    32: 20,
                    33: 24,
                    34: 17,
                    35: 10,
                    36: 22,
                    37: 38,
                    38: 22,
                    39: 8,
                    40: 31,
                    41: 29,
                    42: 25,
                    43: 28,
                    44: 28,
                    45: 25,
                    46: 13,
                    47: 15,
                    48: 22,
                    49: 26,
                    50: 11,
                    51: 23,
                    52: 15,
                    53: 12,
                    54: 17,
                    55: 13,
                    56: 12,
                    57: 21,
                    58: 14,
                    59: 21,
                    60: 22,
                    61: 11,
                    62: 12,
                    63: 19,
                    64: 12,
                    65: 25,
                    66: 24,
                },
            },
        ),
        (
            "BOOK23",
            {
                "chapter_count": 52,
                "verse_counts": {
                    1: 19,
                    2: 37,
                    3: 25,
                    4: 31,
                    5: 31,
                    6: 30,
                    7: 34,
                    8: 22,
                    9: 26,
                    10: 25,
                    11: 23,
                    12: 17,
                    13: 27,
                    14: 22,
                    15: 21,
                    16: 21,
                    17: 27,
                    18: 23,
                    19: 15,
                    20: 18,
                    21: 14,
                    22: 30,
                    23: 40,
                    24: 10,
                    25: 38,
                    26: 24,
                    27: 22,
                    28: 17,
                    29: 32,
                    30: 24,
                    31: 40,
                    32: 44,
                    33: 26,
                    34: 22,
                    35: 19,
                    36: 32,
                    37: 21,
                    38: 28,
                    39: 18,
                    40: 16,
                    41: 18,
                    42: 22,
                    43: 13,
                    44: 30,
                    45: 5,
                    46: 28,
                    47: 7,
                    48: 47,
                    49: 39,
                    50: 46,
                    51: 64,
                    52: 34,
                },
            },
        ),
        ("BOOK24", {"chapter_count": 5, "verse_counts": {1: 22, 2: 22, 3: 66, 4: 22, 5: 22}}),
        (
            "BOOK25",
            {
                "chapter_count": 48,
                "verse_counts": {
                    1: 28,
                    2: 10,
                    3: 27,
                    4: 17,
                    5: 17,
                    6: 14,
                    7: 27,
                    8: 18,
                    9: 11,
                    10: 22,
                    11: 25,
                    12: 28,
                    13: 23,
                    14: 23,
                    15: 8,
                    16: 63,
                    17: 24,
                    18: 32,
                    19: 14,
                    20: 49,
                    21: 32,
                    22: 31,
                    23: 49,
                    24: 27,
                    25: 17,
                    26: 21,
                    27: 36,
                    28: 26,
                    29: 21,
                    30: 26,
                    31: 18,
                    32: 32,
                    33: 33,
                    34: 31,
                    35: 15,
                    36: 38,
                    37: 28,
                    38: 23,
                    39: 29,
                    40: 49,
                    41: 26,
                    42: 20,
                    43: 27,
                    44: 31,
                    45: 25,
                    46: 24,
                    47: 23,
                    48: 35,
                },
            },
        ),
        (
            "BOOK26",
            {
                "chapter_count": 12,
                "verse_counts": {1: 21, 2: 49, 3: 30, 4: 37, 5: 31, 6: 28, 7: 28, 8: 27, 9: 27, 10: 21, 11: 45, 12: 13},
            },
        ),
        (
            "BOOK27",
            {
                "chapter_count": 14,
                "verse_counts": {
                    1: 11,
                    2: 23,
                    3: 5,
                    4: 19,
                    5: 15,
                    6: 11,
                    7: 16,
                    8: 14,
                    9: 17,
                    10: 15,
                    11: 12,
                    12: 14,
                    13: 16,
                    14: 9,
                },
            },
        ),
        ("BOOK28", {"chapter_count": 3, "verse_counts": {1: 20, 2: 32, 3: 21}}),
        (
            "BOOK29",
            {"chapter_count": 9, "verse_counts": {1: 15, 2: 16, 3: 15, 4: 13, 5: 27, 6: 14, 7: 17, 8: 14, 9: 15}},
        ),
        ("BOOK30", {"chapter_count": 1, "verse_counts": {1: 21}}),
        ("BOOK31", {"chapter_count": 4, "verse_counts": {1: 17, 2: 10, 3: 10, 4: 11}}),
        ("BOOK32", {"chapter_count": 7, "verse_counts": {1: 16, 2: 13, 3: 12, 4: 13, 5: 15, 6: 16, 7: 20}}),
        ("BOOK33", {"chapter_count": 3, "verse_counts": {1: 15, 2: 13, 3: 19}}),
        ("BOOK34", {"chapter_count": 3, "verse_counts": {1: 17, 2: 20, 3: 19}}),
        ("BOOK35", {"chapter_count": 3, "verse_counts": {1: 18, 2: 15, 3: 20}}),
        ("BOOK36", {"chapter_count": 2, "verse_counts": {1: 15, 2: 23}}),
        (
            "BOOK37",
            {
                "chapter_count": 14,
                "verse_counts": {
                    1: 21,
                    2: 13,
                    3: 10,
                    4: 14,
                    5: 11,
                    6: 15,
                    7: 14,
                    8: 23,
                    9: 17,
                    10: 12,
                    11: 17,
                    12: 14,
                    13: 9,
                    14: 21,
                },
            },
        ),
        ("BOOK38", {"chapter_count": 4, "verse_counts": {1: 14, 2: 17, 3: 18, 4: 6}}),
        (
            "BOOK39",
            {
                "chapter_count": 28,
                "verse_counts": {
                    1: 25,
                    2: 23,
                    3: 17,
                    4: 25,
                    5: 48,
                    6: 34,
                    7: 29,
                    8: 34,
                    9: 38,
                    10: 42,
                    11: 30,
                    12: 50,
                    13: 58,
                    14: 36,
                    15: 39,
                    16: 28,
                    17: 27,
                    18: 35,
                    19: 30,
                    20: 34,
                    21: 46,
                    22: 46,
                    23: 39,
                    24: 51,
                    25: 46,
                    26: 75,
                    27: 66,
                    28: 20,
                },
            },
        ),
        (
            "BOOK40",
            {
                "chapter_count": 16,
                "verse_counts": {
                    1: 45,
                    2: 28,
                    3: 35,
                    4: 41,
                    5: 43,
                    6: 56,
                    7: 37,
                    8: 38,
                    9: 50,
                    10: 52,
                    11: 33,
                    12: 44,
                    13: 37,
                    14: 72,
                    15: 47,
                    16: 20,
                },
            },
        ),
        (
            "BOOK41",
            {
                "chapter_count": 24,
                "verse_counts": {
                    1: 80,
                    2: 52,
                    3: 38,
                    4: 44,
                    5: 39,
                    6: 49,
                    7: 50,
                    8: 56,
                    9: 62,
                    10: 42,
                    11: 54,
                    12: 59,
                    13: 35,
                    14: 35,
                    15: 32,
                    16: 31,
                    17: 37,
                    18: 43,
                    19: 48,
                    20: 47,
                    21: 38,
                    22: 71,
                    23: 56,
                    24: 53,
                },
            },
        ),
        (
            "BOOK42",
            {
                "chapter_count": 21,
                "verse_counts": {
                    1: 51,
                    2: 25,
                    3: 36,
                    4: 54,
                    5: 47,
                    6: 71,
                    7: 53,
                    8: 59,
                    9: 41,
                    10: 42,
                    11: 57,
                    12: 50,
                    13: 38,
                    14: 31,
                    15: 27,
                    16: 33,
                    17: 26,
                    18: 40,
                    19: 42,
                    20: 31,
                    21: 25,
                },
            },
        ),
        (
            "BOOK43",
            {
                "chapter_count": 28,
                "verse_counts": {
                    1: 26,
                    2: 47,
                    3: 26,
                    4: 37,
                    5: 42,
                    6: 15,
                    7: 60,
                    8: 40,
                    9: 43,
                    10: 48,
                    11: 30,
                    12: 25,
                    13: 52,
                    14: 28,
                    15: 41,
                    16: 40,
                    17: 34,
                    18: 28,
                    19: 41,
                    20: 38,
                    21: 40,
                    22: 30,
                    23: 35,
                    24: 27,
                    25: 27,
                    26: 32,
                    27: 44,
                    28: 31,
                },
            },
        ),
        (
            "BOOK44",
            {
                "chapter_count": 16,
                "verse_counts": {
                    1: 32,
                    2: 29,
                    3: 31,
                    4: 25,
                    5: 21,
                    6: 23,
                    7: 25,
                    8: 39,
                    9: 33,
                    10: 21,
                    11: 36,
                    12: 21,
                    13: 14,
                    14: 23,
                    15: 33,
                    16: 27,
                },
            },
        ),
        (
            "BOOK45",
            {
                "chapter_count": 16,
                "verse_counts": {
                    1: 31,
                    2: 16,
                    3: 23,
                    4: 21,
                    5: 13,
                    6: 20,
                    7: 40,
                    8: 13,
                    9: 27,
                    10: 33,
                    11: 34,
                    12: 31,
                    13: 13,
                    14: 40,
                    15: 58,
                    16: 24,
                },
            },
        ),
        (
            "BOOK46",
            {
                "chapter_count": 13,
                "verse_counts": {
                    1: 24,
                    2: 17,
                    3: 18,
                    4: 18,
                    5: 21,
                    6: 18,
                    7: 16,
                    8: 24,
                    9: 15,
                    10: 18,
                    11: 33,
                    12: 21,
                    13: 14,
                },
            },
        ),
        ("BOOK47", {"chapter_count": 6, "verse_counts": {1: 24, 2: 21, 3: 29, 4: 31, 5: 26, 6: 18}}),
        ("BOOK48", {"chapter_count": 6, "verse_counts": {1: 23, 2: 22, 3: 21, 4: 32, 5: 33, 6: 24}}),
        ("BOOK49", {"chapter_count": 4, "verse_counts": {1: 30, 2: 30, 3: 21, 4: 23}}),
        ("BOOK50", {"chapter_count": 4, "verse_counts": {1: 29, 2: 23, 3: 25, 4: 18}}),
        ("BOOK51", {"chapter_count": 5, "verse_counts": {1: 10, 2: 20, 3: 13, 4: 18, 5: 28}}),
        ("BOOK52", {"chapter_count": 3, "verse_counts": {1: 12, 2: 17, 3: 18}}),
        ("BOOK53", {"chapter_count": 6, "verse_counts": {1: 20, 2: 15, 3: 16, 4: 16, 5: 25, 6: 21}}),
        ("BOOK54", {"chapter_count": 4, "verse_counts": {1: 18, 2: 26, 3: 17, 4: 22}}),
        ("BOOK55", {"chapter_count": 3, "verse_counts": {1: 16, 2: 15, 3: 15}}),
        ("BOOK56", {"chapter_count": 1, "verse_counts": {1: 25}}),
        (
            "BOOK57",
            {
                "chapter_count": 13,
                "verse_counts": {
                    1: 14,
                    2: 18,
                    3: 19,
                    4: 16,
                    5: 14,
                    6: 20,
                    7: 28,
                    8: 13,
                    9: 28,
                    10: 39,
                    11: 40,
                    12: 29,
                    13: 25,
                },
            },
        ),
        ("BOOK58", {"chapter_count": 5, "verse_counts": {1: 27, 2: 26, 3: 18, 4: 17, 5: 20}}),
        ("BOOK59", {"chapter_count": 5, "verse_counts": {1: 25, 2: 25, 3: 22, 4: 19, 5: 14}}),
        ("BOOK60", {"chapter_count": 3, "verse_counts": {1: 21, 2: 22, 3: 18}}),
        ("BOOK61", {"chapter_count": 5, "verse_counts": {1: 10, 2: 29, 3: 24, 4: 21, 5: 21}}),
        ("BOOK62", {"chapter_count": 1, "verse_counts": {1: 13}}),
        ("BOOK63", {"chapter_count": 1, "verse_counts": {1: 15}}),
        ("BOOK64", {"chapter_count": 1, "verse_counts": {1: 25}}),
        (
            "BOOK65",
            {
                "chapter_count": 22,
                "verse_counts": {
                    1: 20,
                    2: 29,
                    3: 22,
                    4: 11,
                    5: 14,
                    6: 17,
                    7: 17,
                    8: 13,
                    9: 21,
                    10: 11,
                    11: 19,
                    12: 17,
                    13: 18,
                    14: 20,
                    15: 8,
                    16: 21,
                    17: 18,
                    18: 24,
                    19: 21,
                    20: 15,
                    21: 27,
                    22: 21,
                },
            },
        ),
    ]
)

# All possible bible book names, normalized (lower case plus other transformations),
# matched to canonical name:
_BIBLE_BOOK_ALTERNATIVES_FOR_LANG = {}

# From https://www.logos.com/bible-book-abbreviations
EN_EXTRA_BOOK_NAMES = """
Genesis
    Gen.
    Ge.
    Gn.

Exodus
    Ex.
    Exod.
    Exo.

Leviticus
    Lev.
    Le.
    Lv.

Numbers
    Num.
    Nu.
    Nm.
    Nb.

Deuteronomy
    Deut.
    De.
    Dt.

Joshua
    Josh.
    Jos.
    Jsh.

Judges
    Judg.
    Jdg.
    Jg.
    Jdgs.

Ruth
    Rth.
    Ru.

1 Samuel
    1 Sam.
    1 Sm.
    1 Sa.
    1 S.
    I Sam.
    I Sa.
    1Sam.
    1Sa.
    1S.
    1st Samuel
    1st Sam.

2 Samuel
    2 Sam.
    2 Sm.
    2 Sa.
    2 S.
    II Sam.
    II Sa.
    2Sam.
    2Sa.
    2S.
    2nd Samuel
    2nd Sam.

1 Kings
    1 Kgs
    1 Ki
    1Kgs
    1Kin
    1Ki
    1K
    I Kgs
    I Ki
    1st Kings
    1st Kgs

2 Kings
    2 Kgs.
    2 Ki.
    2Kgs.
    2Kin.
    2Ki.
    2K.
    II Kgs.
    II Ki.
    2nd Kings
    2nd Kgs.

1 Chronicles
    1 Chron.
    1 Chr.
    1 Ch.
    1Chron.
    1Chr.
    1Ch.
    I Chron.
    I Chr.
    I Ch.
    1st Chronicles
    1st Chron.

2 Chronicles
    2 Chron.
    2 Chr.
    2 Ch.
    2Chron.
    2Chr.
    2Ch.
    II Chron.
    II Chr.
    II Ch.
    2nd Chronicles
    2nd Chron.

Ezra
    Ezra
    Ezr.
    Ez.

Nehemiah
    Neh.
    Ne.

Esther
    Est.
    Esth.
    Es.

Job
    Job
    Jb.

Psalm
    Ps.
    Psalm
    Pslm.
    Psa.
    Psm.
    Pss.
    Psalms

Proverbs
    Prov
    Pro.
    Prv.
    Pr.

Ecclesiastes
    Eccles.
    Eccle.
    Ecc.
    Ec.
    Qoh.

Song of Solomon
    Song.
    Song of Songs
    Songs
    Sg.
    Sng.
    SOS.
    So.
    Canticle of Canticles
    Canticles
    Cant.

Isaiah
    Isa.
    Is.

Jeremiah
    Jer.
    Je.
    Jr.

Lamentations
    Lam.
    La.

Ezekiel
    Ezek.
    Eze.
    Ezk.

Daniel
    Dan.
    Da.
    Dn.

Hosea
    Hos.
    Ho.

Joel
    Jl.

Amos
    Am.

Obadiah
    Obad.
    Ob.

Jonah
    Jonah
    Jnh.
    Jon.

Micah
    Mic.
    Mc.

Nahum
    Nah.
    Na.

Habakkuk
    Hab.
    Hb.

Zephaniah
    Zeph.
    Zep.
    Zp.

Haggai
    Hag.
    Hg.

Zechariah
    Zech.
    Zec.
    Zc.

Malachi
    Mal.
    Ml.

Matthew
    Matt.
    Mt.

Mark
    Mark
    Mrk.
    Mar.
    Mk.
    Mr.

Luke
    Luke
    Luk.
    Lk.

John
    John
    Joh.
    Jhn.
    Jn.

Acts
    Acts
    Act.
    Ac.

Romans
    Rom.
    Ro.
    Rm.

1 Corinthians
    1 Cor.
    1 Co.
    I Cor.
    I Co.
    1Cor.
    1Co.
    I Corinthians
    1Corinthians
    1st Corinthians

2 Corinthians
    2 Cor.
    2 Co.
    II Cor.
    II Co.
    2Cor.
    2Co.
    II Corinthians
    2Corinthians
    2nd Corinthians

Galatians
    Gal.
    Ga.

Ephesians
    Eph.
    Ephes.

Philippians
    Phil.
    Php.
    Pp.

Colossians
    Col.
    Co.

1 Thessalonians
    1 Thess.
    1 Thes.
    1 Th.
    I Thessalonians
    I Thess.
    I Thes.
    I Th.
    1Thessalonians
    1Thess.
    1Thes.
    1Th.
    1st Thessalonians
    1st Thess.

2 Thessalonians
    2 Thess.
    2 Thes.
    2 Th.
    II Thessalonians
    II Thess.
    II Thes.
    II Th.
    2Thessalonians
    2Thess.
    2Thes.
    2Th.
    2nd Thessalonians
    2nd Thess.

1 Timothy
    1 Tim.
    1 Ti.
    I Timothy
    I Tim.
    I Ti.
    1Timothy
    1Tim.
    1Ti.
    1st Timothy
    1st Tim.

2 Timothy
    2 Tim.
    2 Ti.
    II Timothy
    II Tim.
    II Ti.
    2Timothy
    2Tim.
    2Ti.
    2nd Timothy
    2nd Tim.

Titus
    Titus
    Tit
    ti

Philemon
    Philem.
    Phm.
    Pm.

Hebrews
    Heb.

James
    James
    Jas
    Jm

1 Peter
    1 Pet.
    1 Pe.
    1 Pt.
    1 P.
    I Pet.
    I Pt.
    I Pe.
    1Peter
    1Pet.
    1Pe.
    1Pt.
    1P.
    I Peter
    1st Peter

2 Peter
    2 Pet.
    2 Pe.
    2 Pt.
    2 P.
    II Peter
    II Pet.
    II Pt.
    II Pe.
    2Peter
    2Pet.
    2Pe.
    2Pt.
    2P.
    2nd Peter

1 John
    1 John
    1 Jhn.
    1 Jn.
    1 J.
    1John
    1Jhn.
    1Joh.
    1Jn.
    1Jo.
    1J.
    I John
    I Jhn.
    I Joh.
    I Jn.
    I Jo.
    1st John

2 John
    2 John
    2 Jhn.
    2 Jn.
    2 J.
    2John
    2Jhn.
    2Joh.
    2Jn.
    2Jo.
    2J.
    II John
    II Jhn.
    II Joh.
    II Jn.
    II Jo.
    2nd John

3 John
    3 John
    3 Jhn.
    3 Jn.
    3 J.
    3John
    3Jhn.
    3Joh.
    3Jn.
    3Jo.
    3J.
    III John
    III Jhn.
    III Joh.
    III Jn.
    III Jo.
    3rd John

Jude
    Jude
    Jud.
    Jd.

Revelation
    Rev.
"""

NL_EXTRA_BOOK_NAMES = """
Genesis
    Gen.

Exodus
    Éxodus
    Ex.

Leviticus
    Lev.

Numeri
    Num.

Deuteronomium
    Deut.

Jozua
    Joz.

Richteren
    Richt.
    Ri.

Ruth
    Ruth

1 Samuël
    1 Samuel
    1 Sam.

2 Samuël
    2 Samuel
    2 Sam.

1 Koningen
    1 Kon.

2 Koningen
    2 Kon.

1 Kronieken
    1 Kron.
    1 Kr.

2 Kronieken
    2 Kron.
    2 Kr.

Ezra
    Ezra

Nehemia
    Nehémia
    Neh.

Esther
    Ester
    Est.

Job
    Job

Psalm
    Ps.
    Psalmen

Spreuken
    Spr.

Prediker
    Pre.
    Pred.
    Pr.

Hooglied
    Hoogl.

Jesaja
    Jes.

Jeremia
    Jer.

Klaagliederen
    Klaagl.

Ezechiël
    Ezechiel
    Eze.
    Ezech.

Daniël
    Daniel
    Dan.

Hosea
    Hoséa
    Hos.

Joël
    Joel
    Joël

Amos
    Am.

Obadja
    Ob.

Jona
    Jona

Micha
    Mi.
    Mich.

Nahum
    Nah.

Habakuk
    Hábakuk
    Hab.

Zefanja
    Zefánja
    Sefanja
    Zef.
    Sef.

Haggaï
    Haggai
    Hag.

Zacharia
    Zacharía
    Zach.

Maleachi
    Maleáchi
    Mal.

Mattheüs
    Matthéüs
    Mattheus
    Matteüs
    Matt.
    Mat.
    Mt.

Markus
    Marcus
    Mar.
    Mark.
    Marc.

Lukas
    Lucas
    Luk.
    Luc.

Johannes
    Joh.

Handelingen
    Hand.

Romeinen
    Rom.

1 Korinthe
    1 Korinthiërs
    1 Korintiërs
    1 Kor.
    1 Corinthiërs
    1 Corintiërs
    1 Cor.

2 Korinthe
    2 Korinthiërs
    2 Korintiërs
    2 Kor.
    2 Corinthiërs
    2 Corintiërs
    2 Cor.

Galaten
    Gal.

Efeze
    Éfeze
    Efeziërs
    Ef.

Filippenzen
    Fil.

Kolossenzen
    Colossenzen
    Kol.
    Col.

1 Thessalonicenzen
    1 Tessalonicenzen
    1 Thess.
    1 Tess.

2 Thessalonicenzen
    2 Tessalonicenzen
    2 Thess.
    2 Tess.

1 Timotheüs
    1 Timótheüs
    1 Timoteüs
    1 Tim.

2 Timotheüs
    2 Timótheüs
    2 Timoteüs
    2 Tim.

Titus
    Tit.

Filemon
    Filémon
    Filem.

Hebreeën
    Hebreeen
    Heb.
    Hebr.

Jakobus
    Jacobus
    Jak.
    Jac.

1 Petrus
    1 Petr.
    1 Pet.

2 Petrus
    2 Petr.
    2 Pet.

1 Johannes
    1 Joh.

2 Johannes
    2 Joh.

3 Johannes
    3 Joh.

Judas
    Jud.

Openbaring
    Openbaringen
    Apokalyps
    Openb.
    Op.
    Ope.
"""

TR_EXTRA_BOOK_NAMES = """
Yaratılış
    yar
    yarat
    tekvin

Mısır'dan Çıkış
    Mıs
    Mısır
    Mısırdan
    Çıkış

Levililer
    lev
    levi
    levil

Çölde Sayım
    Cölde

Yasa'nın Tekrarı
    yasa
    yasanin
    tesniye

Hâkimler
    hak
    hakim

Rut
    ru
    rut

1. Samuel
    1sa
    1sam
    1samuel
    1 sa
    1 sam
    1 samuel
    1.sa
    1.sam
    1.samuel
    1. sa
    1. sam
    1. samuel

2. Samuel
    2sa
    2sam
    2samuel
    2 sa
    2 sam
    2 samuel
    2.sa
    2.sam
    2.samuel
    2. sa
    2. sam
    2. samuel

1. Krallar
    1kr
    1kra
    1kral
    1 kr
    1 kra
    1 kral
    1.kr
    1.kra
    1.kral
    1. kr
    1. kra
    1. kral

2. Krallar
    2kr
    2kra
    2kral
    2 kr
    2 kra
    2 kral
    2.kr
    2.kra
    2.kral
    2. kr
    2. kra
    2. kral

1. Tarihler
    1ta
    1tar
    1tarih
    1 ta
    1 tar
    1 tarih
    1.ta
    1.tar
    1.tarih
    1. ta
    1. tar
    1. tarih

2. Tarihler
    2ta
    2tar
    2tarih
    2 ta
    2 tar
    2 tarih
    2.ta
    2.tar
    2.tarih
    2. ta
    2. tar
    2. tarih

Ezra
    ezr
    ezra

Nehemya
    ne
    neh
    nehe
    nehem
    nehemy
    nehemya

Ester
    es
    est

Eyüp
    ey

Mezmurlar
    mez
    mezmur
    mz
    zabur

Süleyman'ın Özdeyişleri
    Süleyman
    Süleymanin
    Öz
    Özdeyis

Ezgiler Ezgisi
    ezgi
    ezgiler
    nesiderler
    nesiderler nesidesi

Yeşaya
    Yeş
    Yeşa
    isaya

Yeremya
    yer
    yerem
    yeremya

Ağıtlar
    Ağıt
    Ağıtlar
    yeremyanin
    yeremyanin mersiyeleri
    mersiyeleri
    mersiyeler

Hezekiel
    hez
    hezek

Daniel
    dan

Hoşea
    Ho
    Hoş

Yoel
    yo
    yoel

Amos
    am

Ovadya
    ov
    ovad

Yunus
    yun

Mika
    mik

Nahum
    na
    nah

Habakkuk
    hab
    habak

Sefanya
    sef
    sefan
    tsefanya

Hagay
    hag

Zekeriya
    zek
    zeker
    zekar
    zekarya

Malaki
    mal
    malak

Matta
    mat
    matta

Markos
    mar
    mark

Luka
    lu
    luk

Yuhanna
    yuh
    yuhan
    yhn

Elçilerin İşleri
    Elçi
    Elçiler
    Elçilerin

Romalılar
    ro
    rom
    roma
    romali

1. Korintliler
    1ko
    1kor
    1korintli
    1 ko
    1 kor
    1 korintli
    1.ko
    1.kor
    1.korintli
    1. ko
    1. kor
    1. korintli

2. Korintliler
    2ko
    2kor
    2korintli
    2 ko
    2 kor
    2 korintli
    2.ko
    2.kor
    2.korintli
    2. ko
    2. kor
    2. korintli

Galatyalılar
    gal
    galat
    galatya
    galatyali

Efesliler
    ef
    efes
    efesli


Filipililer
    fil
    filip
    filipili

Koloseliler
    ko
    kol
    kolos
    koloseli

1. Selanikliler
    1se
    1sel
    1selanik
    1selanikli
    1 se
    1 sel
    1 selanik
    1 selanikli
    1.se
    1.sel
    1.selanik
    1.selanikli
    1. se
    1. sel
    1. selanik
    1. selanikli

2. Selanikliler
    2se
    2sel
    2selanik
    2selanikli
    2 se
    2 sel
    2 selanik
    2 selanikli
    2.se
    2.sel
    2.selanik
    2.selanikli
    2. se
    2. sel
    2. selanik
    2. selanikli

1. Timoteos
    1ti
    1tim
    1timoteos
    1 ti
    1 tim
    1 timoteos
    1.ti
    1.tim
    1.timoteos
    1. ti
    1. tim
    1. timoteos

2. Timoteos
    2ti
    2tim
    2timoteos
    2 ti
    2 tim
    2 timoteos
    2.ti
    2.tim
    2.timoteos
    2. ti
    2. tim
    2. timoteos

Titus
    ti
    tit

Filimon
    flm
    filim
    filimo
    filimon

İbraniler
    ib
    ibrani

Yakup
    yak

1. Petrus
    1pe
    1pet
    1petrus
    1 pe
    1 pet
    1 petrus
    1.pe
    1.pet
    1.petrus
    1. pe
    1. pet
    1. petrus

2. Petrus
    2pe
    2pet
    2petrus
    2 pe
    2 pet
    2 petrus
    2.pe
    2.pet
    2.petrus
    2. pe
    2. pet
    2. petrus

1. Yuhanna
    1yu
    1yuh
    1yhn
    1yuhan
    1yuhanna
    1 yu
    1 yuh
    1 yhn
    1 yuhan
    1 yuhanna
    1.yu
    1.yuh
    1.yhn
    1.yuhan
    1.yuhanna
    1. yu
    1. yuh
    1. yhn
    1. yuhan
    1. yuhanna

2. Yuhanna
    2yu
    2yuh
    2yhn
    2yuhan
    2yuhanna
    2 yu
    2 yuh
    2 yhn
    2 yuhan
    2 yuhanna
    2.yu
    2.yuh
    2.yhn
    2.yuhan
    2.yuhanna
    2. yu
    2. yuh
    2. yhn
    2. yuhan
    2. yuhanna

3. Yuhanna
    3yu
    3yuh
    3yhn
    3yuhan
    3yuhanna
    3 yu
    3 yuh
    3 yhn
    3 yuhan
    3 yuhanna
    3.yu
    3.yuh
    3.yhn
    3.yuhan
    3.yuhanna
    3. yu
    3. yuh
    3. yhn
    3. yuhan
    3. yuhanna

Yahuda
    yah
    yahud

Vahiy
    vah
"""

# https://support.logos.com/hc/es/articles/360021229852-Abreviaciones-de-los-libros-de-la-Biblia
ES_EXTRA_BOOK_NAMES = """
Génesis
    Ge
    Gen
    Gn

Éxodo
    Ex
    Exo
    Exod

Levítico
    Le
    Lev
    Lv

Números
    Nm
    Nu
    Num

Deuteronomio
    De
    Deut
    Dt

Josué
    Jos
    Josu
    Js

Jueces
    Ju
    Jue

Rut
    Rt
    Ru

1 Samuel
    1 Sa
    1 Sam
    1 Sm
    1S
    1Sa
    1Sam

2 Samuel
    2 Sa
    2 Sam
    2 Sm
    2S
    2Sa
    2Sam

1 Reyes
    1 Re
    1Re

2 Reyes
    2 Re
    2Re

1 Crónicas
    1 Cr
    1 Crn
    1 Cro
    1 Cron
    1Cr
    1Crn
    1Cro
    1Cron

2 Crónicas
    2 Cr
    2 Crn
    2 Cro
    2 Cron
    2Cr
    2Crn
    2Cro
    2Cron

Esdras
    Esd
    Esdr

Nehemías
    Ne
    Neh

Ester
    Est

Job
    Jb

Salmos
    Sa
    Salm
    Slm
    Sls

Proverbios
    Pr
    Pro
    Prov
    Prv

Eclesiastés
    Ec
    Ecle
    Ecles

El Cantar de los Cantares
    Cant
    Cantar de los Cantares
    Cantares
    Cnt

Isaías
    Is
    Isa

Jeremías
    Je
    Jer
    Jr

Lamentaciones
    La
    Lam

Ezequiel
    Eze
    Ezeq
    Ezq

Daniel
    Da
    Dan
    Dn

Oseas
    Os
    Oss

Joel
    Jl
    Joe

Amós
    Am

Abdías
    Ab
    Abdi

Jonás
    Jns
    Jon

Nahúm
    Na
    Nah

Habacuc
    Hab
    Hab
    Hb

Sofonías
    Sofo
    Sof

Hageo
    Ageo
    Ag
    Hage
    Hag
    Hg

Zacarías
    Zac
    Zc

Malaquías
    Mal
    Mal
    Ml

Mateo
    Mat
    Mt

Marcos
    Mrc
    Mar
    Mc
    Mr

Lucas
    Lc
    Luc

Juan
    Jn
    Jua

Hechos
    Hch
    Hec
    Hechos de los Apóstoles

Romanos
    Ro
    Rom

1 Corintios
    1 Co
    1 Cor
    1Co
    1Cor
    1Corintios

2 Corintios
    2 Co
    2 Cor
    2Co
    2Cor
    2Corintios

Gálatas
    Ga
    Gal

Efesios
    Ef
    Efes

Filipenses
    Fi
    Fil
    Fili
    Flp

Colosenses
    Co
    Col

1 Tesalonicenses
    1 Tes
    1 Ts
    1Tes
    1Tesalonicenses
    1Ts

2 Tesalonicenses
    2 Tes
    2 Ts
    2Tes
    2Tesalonicenses
    2Ts

1 Timoteo
    1 Ti
    1 Tim
    1Ti
    1Tim
    1Timoteo

2 Timoteo
    2 Ti
    2 Tim
    2Ti
    2Tim
    2Timoteo

Tito
    Ti
    Tit

Filemón
    Filem
    Film
    Flm

Hebreos
    Heb

Santiago
    Sant
    Stg

1 Pedro
    1 P
    1 Pd
    1 Pe
    1 Ped
    1P
    1Pd
    1Pe
    1Ped
    1Pedro

2 Pedro
    2 P
    2 Pd
    2 Pe
    2 Ped
    2P
    2Pd
    2Pe
    2Ped
    2Pedro

1 Juan
    1 Jn
    1J
    1Jn
    1Juan

2 Juan
    2 Jn
    2J
    2Jn
    2Juan

3 Juan
    3 Jn
    3J
    3Jn
    3Juan

Judas
    Jd
    Jud

Apocalipsis
    Ap
    Apo
    Apoc
"""

def parse_abbrev_def(abbrev_def):
    # -- Parser for the above format:
    book_name = P.regex(r"\S[^\n]+")
    abbrev = P.regex(r" +([^\n]+)", group=1)
    empty = P.regex(r"\s*")
    NL = P.string("\n")
    parser = (P.seq(book_name << NL, (abbrev << NL).many()) << empty).many()
    return parser.parse(abbrev_def.lstrip())


def make_bible_book_abbreviations():
    for code, abbrev_def in [
        (LANG.EN, EN_EXTRA_BOOK_NAMES),
        (LANG.TR, TR_EXTRA_BOOK_NAMES),
        (LANG.NL, NL_EXTRA_BOOK_NAMES),
        (LANG.ES, ES_EXTRA_BOOK_NAMES),
    ]:
        parsed = parse_abbrev_def(abbrev_def)
        _BIBLE_BOOK_ALTERNATIVES_FOR_LANG[code] = {}
        for book_name in _BIBLE_BOOKS_FOR_LANG[code]:
            _BIBLE_BOOK_ALTERNATIVES_FOR_LANG[code][normalize_reference_input(code, book_name)] = book_name

        for book_name, abbrevs in parsed:
            if book_name not in _BIBLE_BOOKS_FOR_LANG[code]:
                raise AssertionError(f"Book {book_name} not known")
            adjusted_abbrevs = []
            for abbrev in set(abbrevs):
                abbrev = normalize_reference_input(code, abbrev.lower())
                adjusted_abbrevs.append(abbrev)
                if abbrev.endswith("."):
                    adjusted_abbrevs.append(abbrev.rstrip("."))
            for abbrev in adjusted_abbrevs:
                if abbrev in _BIBLE_BOOK_ALTERNATIVES_FOR_LANG[code]:
                    if abbrev == normalize_reference_input(code, book_name.lower()):
                        # ignore without complaining
                        continue
                    else:
                        raise AssertionError(f"Duplicate for abbreviation {abbrev}")
                _BIBLE_BOOK_ALTERNATIVES_FOR_LANG[code][abbrev] = book_name


def checks():
    for lang, books in _BIBLE_BOOKS_FOR_LANG.items():
        if len(books) != BIBLE_BOOK_COUNT:
            raise AssertionError(f"Language {lang} doesn't have the expected number of Bible books defined!")


make_bible_book_abbreviations()
checks()
