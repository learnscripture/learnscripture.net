import re
import subprocess

from bibleverses.models import Verse, BibleVersion

DIATHEKE = '/home/luke/tmpstore/build/sword-1.6.1/utilities/diatheke/diatheke'

BIBLE_BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']

def get_book(version, book):
    out = subprocess.check_output([DIATHEKE, '-b', version, '-k', book])
    verses = {}
    verse = []
    verse_ref = None
    for line in out.decode('utf-8').split('\n'):

        match = re.match('(((I+ )?[a-z]+ \d+:\d+): (.*))', line, re.IGNORECASE)
        if match:
            # deal with old
            if verse and verse_ref :
                verses[verse_ref] = ('\n'.join(verse)).strip()
                verse = []
            verse_ref = match.groups()[1]
            verse.append(match.groups()[3])
        else:
            if line.strip() == "(%s)" % version:
                if verse and verse_ref:
                    verses[verse_ref] = ('\n'.join(verse)).strip()
                verse_ref = None
                verse = []
            if verse_ref:
                verse.append(line)
    if verse and verse_ref:
        verses[verse_ref] = ('\n'.join(verse)).strip()

    return verses


def import_bible(version):
    version_obj = BibleVersion.objects.get(short_name=version)
    for b in BIBLE_BOOKS:
        verses = get_book(version, b)
        for ref, text in sorted(verses.items()):
            # Fixes:
            ref = ref.replace('Psalms', 'Psalm')
            ref = re.sub('^I ', '1 ', ref)
            ref = re.sub('^II ', '2 ', ref)
            text = text.replace('.', '. ').replace('.  ', '. ')
            v, x = Verse.objects.get_or_create(version=version_obj,
                                               reference=ref)
            v.text = text
            v.save()



