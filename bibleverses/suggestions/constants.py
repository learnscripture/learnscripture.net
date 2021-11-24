# -- Bible handling

TORAH = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]

HISTORY = [
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

WISDOM = ["Job", "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon"]

PROPHETS = [
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

NT_HISTORY = ["Matthew", "Mark", "Luke", "John", "Acts"]

EPISTLES = [
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

BIBLE_BOOK_GROUPS = [TORAH, HISTORY, WISDOM, PROPHETS, NT_HISTORY, EPISTLES]


def similar_books(book_name):
    """
    Return a list of similar Bible books to the passed in book name
    """
    retval = []
    for g in BIBLE_BOOK_GROUPS:
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


def markov_analysis_for_size(size):
    return {1: MARKOV_1_ANALYSIS, 2: MARKOV_2_ANALYSIS, 3: MARKOV_3_ANALYSIS}[size]


# Key to indicate the whole of a text is to be used
ALL_TEXT = "all"
