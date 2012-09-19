import re
import subprocess

from bibleverses.models import Verse, TextVersion

DIATHEKE = '/home/luke/tmpstore/build/sword-1.6.1/utilities/diatheke/diatheke'

BIBLE_BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']


def get_book(version, book):
    out = subprocess.check_output([DIATHEKE, '-b', version, '-k', book])
    verses = []
    verse = []
    verse_ref = None

    def save():
        verses.append((verse_ref, ('\n'.join(verse)).strip()))

    for line in out.decode('utf-8').split('\n'):

        match = re.match('(([a-z ]+ \d+:\d+): (.*))', line, re.IGNORECASE)
        if match:
            # deal with old
            if verse and verse_ref:
                save()
                verse = []
            verse_ref = match.groups()[1]
            verse.append(match.groups()[2])
        else:
            if line.strip() == "(%s)" % version:
                if verse and verse_ref:
                    save()
                verse_ref = None
                verse = []
            if verse_ref:
                verse.append(line)
    if verse and verse_ref:
        save()

    return verses


def fix_ref(ref):
    ref = ref.replace('Psalms', 'Psalm')
    ref = ref.replace('Revelation of John', 'Revelation')
    ref = re.sub('^I ', '1 ', ref)
    ref = re.sub('^II ', '2 ', ref)
    ref = re.sub('^III ', '3 ', ref)
    return ref


def fix_text(text):
    text = text.replace('.', '. ').replace('.  ', '. ')
    # Some stray " at end of verses.
    text = re.sub(' "(\b|$)', '"', text)
    return text

def parse_ref(ref):
    r = ref.rsplit(' ', 1)
    c, v = map(int, r[1].split(':'))
    return r[0], c, v


def import_bible(version):
    version_obj = TextVersion.objects.get(short_name=version)
    get_bible_verse_numbers()

    for b_num, book in enumerate(BIBLE_BOOKS):
        verses = get_book(version, book)
        for ref, text in verses:
            # Fixes:
            ref = fix_ref(ref)
            text = fix_text(text)
            parsed_book, ch_num, v_num = parse_ref(ref)
            assert parsed_book == book
            v, x = Verse.objects.get_or_create(version=version_obj,
                                               reference=ref,
                                               book_number=b_num,
                                               chapter_number=ch_num,
                                               verse_number=v_num,
                                               bible_verse_number=_bible_verse_numbers[ref]
                                               )

            v.text = text

            v.save()


_bible_verse_numbers = {}

def get_bible_verse_numbers():
    if _bible_verse_numbers:
        return _bible_verse_numbers

    i = 0
    for book in BIBLE_BOOKS:
        verses = get_book('KJV', book)
        for ref, text in verses:
            ref = fix_ref(ref)
            p_book, c, v = parse_ref(ref)
            assert p_book == book, "%s = %s" % (p_book, book)
            _bible_verse_numbers[fix_ref(ref)] = i
            i += 1
    return _bible_verse_numbers
