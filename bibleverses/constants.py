from collections import defaultdict


BIBLE_BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']
BIBLE_BOOKS_DICT = dict((n, i) for (i, n) in enumerate(BIBLE_BOOKS))


# All possible bible book names, lower case, matched to canonical name
BIBLE_BOOK_ABBREVIATIONS = {}


def make_bible_book_abbreviations():
    global BIBLE_BOOK_ABBREVIATIONS

    nums = {'1 ': ['1', 'I ', 'I'],
            '2 ': ['2', 'II ', 'II'],
            '3 ': ['3', 'III ', 'III']
            }

    def get_abbrevs(book_name):
        # Get alternatives like '1Peter', 'I Peter' etc.
        for k, v in nums.items():
            if book_name.startswith(k):
                for prefix in v:
                    book_name2 = prefix + book_name[len(k):]
                    for n in get_abbrevs(book_name2):
                        yield n

        # We don't allow abbreviations less than 3 letters
        for i in range(2, len(book_name) + 1):
            yield book_name[0:i]

    # Get all abbreviations
    d = {}
    for b in BIBLE_BOOKS:
        d[b] = list(get_abbrevs(b.lower()))

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

    BIBLE_BOOK_ABBREVIATIONS.update(d3)

    # Some special cases that don't fit above pattern
    BIBLE_BOOK_ABBREVIATIONS.update({
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
        'rm': 'Romans',
        'sg': 'Song of Solomon',
        'sng': 'Song of Solomon',
    })


make_bible_book_abbreviations()
