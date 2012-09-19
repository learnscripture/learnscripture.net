from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import math
import re

from autoslug import AutoSlugField
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models import F
from django.utils import timezone
from django.utils.functional import cached_property

# TextVersion and Verse are pseudo static, so make extensive use of caching.
# VerseSets and VerseChoices also rarely change, and it doesn't matter too much
# if they do, so make liberal use of caching.  Other models won't benefit so
# much due to lots of writes and an increased risk if things go wrong.
import caching.base

from accounts import memorymodel
from bibleverses.fields import VectorField
from learnscripture.datastructures import make_choices


BIBLE_BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']
BIBLE_BOOKS_DICT = dict((n, i) for (i, n) in enumerate(BIBLE_BOOKS))


# All possible bible book names, lower case, matched to canonical name
BIBLE_BOOK_ABBREVIATIONS = {}

def make_bible_book_abbreviations():
    global BIBLE_BOOK_ABBREVIATIONS

    nums = {'1 ':['1', 'I ', 'I'],
            '2 ':['2', 'II ', 'II'],
            '3 ':['3', 'III ', 'III']
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
            'jas': 'James',
            'jm': 'James',
            'jn': 'John',
            'jnh': 'Jonah',
            'jsh': 'Joshua',
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
            })

make_bible_book_abbreviations()

# Psalm 119 is 176 verses
MAX_VERSE_QUERY_SIZE = 200
MAX_VERSES_FOR_SINGLE_CHOICE = 4 # See also choose.js


# Also defined in learn.js
VerseSetType = make_choices('VerseSetType',
                            [(1, 'SELECTION', 'Selection'),
                             (2, 'PASSAGE', 'Passage'),
                            ])

StageType = make_choices('StageType',
                         [(1, 'READ', 'read'),
                          (2, 'RECALL_INITIAL', 'recall from initials'),
                          (3, 'RECALL_MISSING', 'recall when missing'),
                          (4, 'TEST', 'test'), # Also used in learn.js
                          ])


# Various queries make use of the ordering in this enum, e.g. select everything
# less than 'TESTED'
MemoryStage = make_choices('MemoryStage',
                           [(1, 'ZERO', 'nothing'),
                            (2, 'SEEN', 'seen'),
                            (3, 'TESTED', 'tested'),
                            (4, 'LONGTERM', 'long term memory'),
                            ])


TextType = make_choices('TextType',
                        [(1, 'BIBLE', 'Bible'),
                         (2, 'CATECHISM', 'Catechism'),
                         ])

class TextVersionManager(caching.base.CachingManager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)


class TextVersion(caching.base.CachingMixin, models.Model):
    short_name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255, unique=True)
    url = models.URLField(default="", blank=True)
    text_type = models.PositiveSmallIntegerField(choices=TextType.choice_list,
                                                 default=TextType.BIBLE)
    description = models.TextField(blank=True)

    public = models.BooleanField(default=True)

    objects = TextVersionManager()

    class Meta:
        ordering = ('short_name',)

    def __unicode__(self):
        return "%s (%s)" % (self.short_name, self.full_name)

    def natural_key(self):
        return (self.slug,)

    def get_verse_list(self, reference, max_length=MAX_VERSE_QUERY_SIZE):
        return parse_ref(reference, self, max_length=max_length)

    def get_text_by_reference(self, reference, max_length=MAX_VERSE_QUERY_SIZE):
        return u' '.join([v.text for v in self.get_verse_list(reference, max_length=max_length)])

    def get_text_by_reference_bulk(self, reference_list):
        """
        Returns a dictionary of {ref:text} for each ref in reference_list. Bad
        references are silently discarded, and won't be in the return
        dictionary.
        """
        verse_dict = self.get_verses_by_reference_bulk(reference_list)
        return dict((ref, v.text) for (ref, v) in verse_dict.items())

    def get_verses_by_reference_bulk(self, reference_list):
        """
        Returns a dictionary of {ref:verse} for each ref in reference_list. Bad
        references are silently discarded, and won't be in the return
        dictionary.
        """
        # We try to do this efficiently, but it is hard for combo references. So
        # we do the easy ones the easy way:
        simple_verses = list(self.verse_set.filter(reference__in=reference_list))
        v_dict = dict((v.reference, v) for v in simple_verses)
        # Now get the others:
        for ref in reference_list:
            if ref not in v_dict:
                try:
                    v_dict[ref] = ComboVerse(ref, self.get_verse_list(ref))
                except InvalidVerseReference:
                    pass
        return v_dict


class ComboVerse(object):
    """
    Wrapper needed when we want a combination of verses to appear as a single
    verse.
    """
    def __init__(self, reference, verse_list):
        self.reference = reference
        self.book_name = verse_list[0].book_name
        self.chapter_number = verse_list[0].chapter_number
        self.verse_number = verse_list[0].verse_number
        self.bible_verse_number = verse_list[0].bible_verse_number
        self.verses = verse_list
        self.text = ' '.join(v.text for v in verse_list)


def intersperse(iterable, delimiter):
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x

class VerseManager(caching.base.CachingManager):

    def text_search(self, query, version, limit=10):
        words = query.split(u' ')
        # Do an 'AND' on all terms
        word_params = list(intersperse(words, ' & '))
        search_clause = ' || ' .join(['%s'] * len(word_params))
        return models.Manager.raw(self, """
          SELECT id, version_id, reference, text,
                 ts_headline(text, query, 'StartSel = **, StopSel = **, HighlightAll=TRUE') as highlighted_text,
                 book_number, chapter_number, verse_number,
                 bible_verse_number, ts_rank(text_tsv, query) as rank
          FROM bibleverses_verse, to_tsquery(""" + search_clause + """) query
          WHERE
             query @@ text_tsv
             AND version_id = %s
          ORDER BY rank DESC
          LIMIT %s;
""", word_params + [version.id, limit])


class Verse(caching.base.CachingMixin, models.Model):
    version = models.ForeignKey(TextVersion)
    reference = models.CharField(max_length=100)
    text = models.TextField()
    text_tsv = VectorField()

    # De-normalised fields
    # Public facing fields are 1-indexed, others are 0-indexed.
    book_number = models.PositiveSmallIntegerField() # 0-indexed
    chapter_number = models.PositiveSmallIntegerField() # 1-indexed
    verse_number = models.PositiveSmallIntegerField()   # 1-indexed
    bible_verse_number = models.PositiveSmallIntegerField() # 0-indexed

    objects = VerseManager()

    @property
    def book_name(self):
        return BIBLE_BOOKS[self.book_number]

    def is_last_verse_in_chapter(self):
        return not self.version.verse_set.filter(
            book_number=self.book_number,
            chapter_number=self.chapter_number,
            verse_number__gt=self.verse_number).exists()

    def __unicode__(self):
        return u"%s (%s)" % (self.reference, self.version.short_name)

    def __repr__(self):
        return u'<Verse %s>' % self

    class Meta:
        unique_together = [
            ('bible_verse_number', 'version'),
            ('reference', 'version'),
            ]
        ordering = ('bible_verse_number',)


class QAPair(models.Model):
    """
    A question/answer pair in a catechism.
    """
    catechism = models.ForeignKey(TextVersion)
    reference = models.CharField(max_length=100)
    question = models.TextField()
    answer = models.TextField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [('catechism', 'order'),
                           ('catechism', 'reference')]

        verbose_name = "QA pair"

    def __unicode__(self):
        return self.reference + " " + self.question


class VerseSetManager(models.Manager):
    def public(self):
        return self.get_query_set().filter(public=True)

    def popularity_for_sets(self, ids, ignoring_account_ids):
        """
        Gets the 'popularity' for a group of sets, using actual usage.
        """
        if len(ids) == 0:
            return 0
        sql = """
SELECT COUNT(*) FROM

  (SELECT uvs.for_identity_id
   FROM
      bibleverses_userversestatus as uvs
      INNER JOIN accounts_identity
      ON accounts_identity.id = uvs.for_identity_id

   WHERE
         uvs.ignored = FALSE
     AND accounts_identity.account_id IS NOT NULL
     AND accounts_identity.account_id NOT in %s
     AND uvs.verse_set_id IN %s

   GROUP BY uvs.for_identity_id
 ) as q
"""
        cursor = connection.cursor()
        cursor.execute(sql, [tuple(ignoring_account_ids), tuple(ids)])
        return cursor.fetchall()[0][0]


class VerseSet(models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='name', unique=True)
    description = models.TextField(blank=True)
    additional_info = models.TextField(blank=True)
    set_type = models.PositiveSmallIntegerField(choices=VerseSetType.choice_list)

    public = models.BooleanField(default=False)
    breaks = models.CharField(max_length=255, default='', blank=True)

    popularity = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey('accounts.Account', related_name='verse_sets_created')

    # Essentially denormalised field, to make it quick to check for duplicate
    # passage sets:
    passage_id = models.CharField(max_length=203, # 100 for reference * 2 + 3 for ' - '
                                  default="")

    objects = VerseSetManager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('view_verse_set', kwargs=dict(slug=self.slug))

    @property
    def is_passage(self):
        return self.set_type == VerseSetType.PASSAGE

    @property
    def breaks_formatted(self):
        return self.breaks.replace(",", ", ")

    @property
    def uncached_verse_choices(self):
        return VerseChoice.uncached_objects.filter(verse_set=self).order_by('set_order')

    def set_verse_choices(self, ref_list):
        # Need to ensure that we preserve existing objects and to do the
        # query correctly we need to ignore caching.
        existing_vcs = self.uncached_verse_choices.all()
        existing_vcs_dict = dict((vc.reference, vc) for vc in existing_vcs)
        old_vcs = set(existing_vcs)
        for i, ref in enumerate(ref_list):  # preserve order
            dirty = False
            if ref in existing_vcs_dict:
                vc = existing_vcs_dict[ref]
                if vc.set_order != i:
                    vc.set_order = i
                    dirty = True
                old_vcs.remove(vc)
            else:
                vc = VerseChoice(verse_set=self,
                                 reference=ref,
                                 set_order=i)
                dirty = True
            if dirty:
                vc.save()

        # Delete unused VerseChoice objects.
        for vc in old_vcs:
            vc.delete()

        self.update_passage_id()

    def update_passage_id(self):
        if self.set_type == VerseSetType.PASSAGE:
            verse_choices = list(self.uncached_verse_choices.all())
            self.passage_id = verse_choices[0].reference + u' - ' + verse_choices[-1].reference
            self.save()


class VerseChoiceManager(caching.base.CachingManager):
    use_for_related_fields = True

    def get_query_set(self):
        return super(VerseChoiceManager, self).get_query_set().order_by('set_order')



# Note that VerseChoice and Verse are not related, since we want a VerseChoice
# to be independent of Bible version.
class VerseChoice(caching.base.CachingMixin, models.Model):
    reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, related_name='verse_choices')
    set_order = models.PositiveSmallIntegerField(default=0)

    objects = VerseChoiceManager()
    uncached_objects = models.Manager()

    class Meta:
        unique_together = [('verse_set', 'reference')]

    def __unicode__(self):
        return self.reference

    def __repr__(self):
        return u'<VerseChoice %s>' % self


class UserVerseStatus(models.Model):
    """
    Tracks the user's progress for a verse.
    """
    # It actually tracks the progress for a VerseChoice and Version.  This
    # implicitly allows it to track progress separately for different versions
    # and for the same verse in different verse sets.  In some cases this is
    # useful (for learning a passage, you might be learning a different version
    # to normal), but usually it is confusing, so business logic limits how much
    # this can happen

    for_identity = models.ForeignKey('accounts.Identity', related_name='verse_statuses')
    reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, null=True,
                                  on_delete=models.SET_NULL)
    bible_verse_number = models.PositiveSmallIntegerField()
    version = models.ForeignKey(TextVersion)
    memory_stage = models.PositiveSmallIntegerField(choices=MemoryStage.choice_list,
                                                    default=MemoryStage.ZERO)
    strength = models.FloatField(default=0.00)
    added = models.DateTimeField()
    first_seen = models.DateTimeField(null=True, blank=True)
    last_tested = models.DateTimeField(null=True, blank=True)
    next_test_due = models.DateTimeField(null=True, blank=True)

    # See Identity.change_version for explanation of ignored
    ignored = models.BooleanField(default=False)


    @cached_property
    def text(self):
        return self.version.get_text_by_reference(self.reference)

    @property
    def needs_testing(self):
        if hasattr(self, 'needs_testing_override'):
            return self.needs_testing_override
        else:
            return self.needs_testing_by_db

    @cached_property
    def needs_testing_by_db(self):
        # We go by 'next_test_due', since that is how we do filtering.
        if self.last_tested is None:
            return True
        if self.next_test_due is None:
            return True
        return timezone.now() >= self.next_test_due

    def is_in_passage(self):
        return self.verse_set is not None and self.verse_set.is_passage

    def simple_strength(self):
        """
        Returns the strength normalised to a 0 to 10 scale for presentation in UI.
        """
        return min(10, int(math.floor((self.strength / memorymodel.LEARNT) * 10)))

    @cached_property
    def passage_reference(self):
        """
        Returns the reference for the whole passage this UVS belongs to.
        """
        if not self.is_in_passage():
            return None
        verse_choices = self.set_verse_choices
        return pretty_passage_ref(verse_choices[0].reference,
                                  verse_choices[-1].reference)

    @cached_property
    def set_verse_choices(self):
        return list(self.verse_set.verse_choices.all())

    @cached_property
    def section_reference(self):
        """
        Returns the reference for the section in the passage this UVS belongs to.
        """
        if not self.is_in_passage():
            return None

        section = self.get_section_verse_choices()
        if section is not None:
            return pretty_passage_ref(section[0].reference,
                                      section[-1].reference)
        return None # Shouldn't get here

    def get_section_verse_choices(self):
        # Split verse set into sections
        sections = get_passage_sections(self.set_verse_choices, self.verse_set.breaks)

        # Now we've got to find which one we are in:
        for section in sections:
            for vc in section:
                if vc.reference == self.reference:
                    return section


    def __unicode__(self):
        return u"%s, %s" % (self.reference, self.version.slug)

    def __repr__(self):
        return u'<UserVerseStatus %s>' % self

    class Meta:
        unique_together = [('for_identity', 'verse_set', 'reference', 'version')]


class InvalidVerseReference(ValueError):
    pass


class Reference(object):
    def __init__(self, book, chapter_number, verse_number):
        self.book = book
        self.chapter_number = chapter_number
        self.verse_number = verse_number

    def __eq__(self, other):
        return (self.book == other.book and
                self.chapter_number == other.chapter_number and
                self.verse_number == other.verse_number)

    def __repr__(self):
        return "<Reference %s %d:%d>" % (self.book, self.chapter_number, self.verse_number)


def parse_ref(reference, version, max_length=MAX_VERSE_QUERY_SIZE,
              return_verses=True):
    """
    Takes a reference and returns the verses referred to in a list.

    If return_verses is False, then the version is not needed, more lenient
    checking is done (the input is trusted), and a Reference object is returned
    instead, or a two tuple (start Reference, end Reference)
    """
    # This function is strict, and expects reference in normalised format.
    # Frontend function should deal with tolerance, to ensure that VerseChoice
    # only ever stores a canonical form.

    # This function will InvalidVerseReference if a verse is not matched.

    if ':' not in reference:
        # chapter only
        try:
            # If there is a space in name, we need this:
            if reference in BIBLE_BOOKS_DICT:
                # no chapter.
                raise ValueError()
            # If no, space, the following will weed out references without a chapter
            book, chapter = reference.rsplit(u' ', 1)
        except ValueError:
            raise InvalidVerseReference(u"Reference should provide at least book name and chapter number")
        if book not in BIBLE_BOOKS_DICT:
            raise InvalidVerseReference(u"Book '%s' not known" % book)
        book_number = BIBLE_BOOKS_DICT.get(book)
        try:
            chapter_number = int(chapter)
        except ValueError:
            raise InvalidVerseReference(u"Expecting '%s' to be a chapter number" % chapter)
        if return_verses:
            retval = list(version.verse_set.filter(book_number=book_number, chapter_number=chapter_number))
        else:
            retval = Reference(book, chapter_number, None)
    else:
        parts = reference.rsplit(u'-', 1)
        if len(parts) == 1:
            # e.g. Genesis 1:1
            if return_verses:
                retval = list(version.verse_set.filter(reference=reference))
            else:
                book, rest = reference.rsplit(' ', 1)
                ch_num, v_num = rest.split(':', 1)
                retval = Reference(book, int(ch_num), int(v_num))
        else:
            # e.g. Genesis 1:1-2
            book, start = parts[0].rsplit(u' ', 1)
            end = parts[1]
            if u':' not in start:
                raise InvalidVerseReference(u"Expecting to find ':' in part '%s'" % start)

            start_chapter, start_verse = start.split(u':')
            try:
                start_chapter = int(start_chapter)
            except ValueError:
                raise InvalidVerseReference(u"Expecting '%s' to be a chapter number" % start_chapter)

            try:
                start_verse = int(start_verse)
            except ValueError:
                raise InvalidVerseReference(u"Expecting '%s' to be a verse number" % start_verse)
            if u':' in end:
                end_chapter, end_verse = end.split(':')
                try:
                    end_chapter = int(end_chapter)
                except ValueError:
                    raise InvalidVerseReference(u"Expecting '%s' to be a chapter number" % end_chapter)
                try:
                    end_verse = int(end_verse)
                except ValueError:
                    raise InvalidVerseReference(u"Expecting '%s' to be a verse number" % end_verse)

            else:
                end_chapter = start_chapter
                try:
                    end_verse = int(end)
                except ValueError:
                    raise InvalidVerseReference(u"Expecting '%s' to be a verse number" % end)

            ref_start = u"%s %d:%d" % (book, start_chapter, start_verse)
            ref_end = u"%s %d:%d" % (book, end_chapter, end_verse)

            if ref_end == ref_start:
                raise InvalidVerseReference("Start and end verse are the same.")

            if return_verses:
                # Try to get results in just two queries
                vs = version.verse_set.filter(reference__in=[ref_start, ref_end])
                try:
                    verse_start = [v for v in vs if v.reference == ref_start][0]
                except IndexError:
                    raise InvalidVerseReference(u"Can't find  '%s'" % ref_start)
                try:
                    verse_end = [v for v in vs if v.reference == ref_end][0]
                except IndexError:
                    raise InvalidVerseReference(u"Can't find  '%s'" % ref_end)

                if verse_end.bible_verse_number < verse_start.bible_verse_number:
                    raise InvalidVerseReference("%s and %s are not in ascending order." % (ref_start, ref_end))

                if verse_end.bible_verse_number - verse_start.bible_verse_number > max_length:
                    raise InvalidVerseReference(u"References that span more than %d verses are not allowed in this context." % max_length)

                retval = list(version.verse_set.filter(bible_verse_number__gte=verse_start.bible_verse_number,
                                                       bible_verse_number__lte=verse_end.bible_verse_number))
            else:
                retval = (Reference(book, start_chapter, start_verse),
                          Reference(book, end_chapter, end_verse))

    if return_verses:
        if len(retval) == 0:
            raise InvalidVerseReference(u"No verses matched '%s'." % reference)

        if len(retval) > max_length:
            raise InvalidVerseReference(u"References that span more than %d verses are not allowed in this context." % max_length)

    return retval


def pretty_passage_ref(start_ref, end_ref):
    first = parse_ref(start_ref, None, return_verses=False)
    last = parse_ref(end_ref, None, return_verses=False)

    ref = u"%s %d:%d" % (first.book,
                         first.chapter_number,
                         first.verse_number,
                         )
    if last.chapter_number == first.chapter_number:
        ref += u"-%d" % last.verse_number
    else:
        ref += u"-%d:%d" % (last.chapter_number, last.verse_number)
    return ref


def get_passage_sections(verse_list, breaks):
    """
    Given a list of objects with a correct 'reference' attribute, and a comma
    separated list of 'break definitions', each of which could be <verse_number>
    or <chapter_number>:<verse_number>, return the list in sections.
    """
    # Since the input has been sanitised, we can do parsing without needing DB
    # queries.

    # First need to parse 'breaks' into a list of References.

    if len(verse_list) == 0:
        return []

    if breaks == '':
        return [verse_list]

    break_list = []

    # First reference provides the context for the breaks.
    first_ref = parse_ref(verse_list[0].reference, None, return_verses=False)
    if isinstance(first_ref, tuple):
        first_ref = first_ref[0]

    verse_number = first_ref.verse_number
    chapter_number = first_ref.chapter_number
    book = first_ref.book
    for b in breaks.split(','):
        b = b.strip()
        if ':' in b:
            chapter_number, verse_number = b.split(':', 1)
            chapter_number = int(chapter_number)
            verse_number = int(verse_number)
        else:
            verse_number = int(b)
        break_list.append(Reference(book, chapter_number, verse_number))

    sections = []
    current_section = []
    for v in verse_list:
        ref = parse_ref(v.reference, None, return_verses=False)
        if isinstance(ref, tuple):
            ref = ref[0]
        if ref in break_list and len(current_section) > 0:
            # Start new section
            sections.append(current_section)
            current_section = []
        current_section.append(v)
    sections.append(current_section)
    return sections


def quick_find(query, version, max_length=MAX_VERSES_FOR_SINGLE_CHOICE,
               allow_searches=True):
    """
    Does a verse search based on reference or contents.

    It returns a list of ComboVerse objects.
    """
    # Unlike parse_ref, this is tolerant with input. It can still throw
    # InvalidVerseReference for things that are obviously incorrect e.g. Psalm
    # 151, or asking for too many verses.

    query = query.strip().lower()

    if query == u'':
        raise InvalidVerseReference("Please enter a query term or reference")

    bible_ref_re = (
        '^.*'                # book name
        '\d+'                # chapter
        '\s*((v|:|\.)'       # optionally: v or : or .
        '\s*\d+'             #             and start verse number
        '(\s*-\s*\d+)?)?$'   #             and optionally end verse
        )


    # Need to work out if this is probably a reference
    if re.match(bible_ref_re, query) or query in BIBLE_BOOK_ABBREVIATIONS:
        reference = normalise_reference(query)
        if reference is not None:
            return [ComboVerse(reference, parse_ref(reference, version, max_length=max_length))]

    if not allow_searches:
        raise InvalidVerseReference("Verse reference not recognised")

    # Do a search:
    results = Verse.objects.text_search(query, version, limit=11)
    return [ComboVerse(r.reference, [r]) for r in results]


def normalise_reference(query):
    # Replace 'v' or '.' with ':'
    query = re.sub(u'(?<![A-Za-z])(v|\.)(?![A-Za-z])', ':', query)
    # Remove spaces around ':'
    query = re.sub(u'\s*:\s*', ':', query)
    # Remove spaces around '-'
    query = re.sub(u'\s*-\s*', '-', query)

    # Remove multiple spaces
    query = re.sub(u' +', u' ', query)

    # Normalise book names if possible.
    parts = query.split(u' ')
    book_name = parts[0]
    if len(parts) > 1 and not re.search(u'\d', parts[1]):
        book_name = book_name + u" " + parts[1]

    if book_name in BIBLE_BOOK_ABBREVIATIONS:
        remainder = query[len(book_name):]
        return BIBLE_BOOK_ABBREVIATIONS[book_name] + remainder
    else:
        return None


def get_verses_started_counts(identity_ids, started_since=None):
    sql = """
SELECT for_identity_id, COUNT(id)
FROM bibleverses_userversestatus
WHERE
    ignored = False
AND memory_stage >= %s
AND for_identity_id IN %s
AND first_seen > %s
GROUP BY for_identity_id
"""
    if started_since is None:
        started_since = datetime(1970, 1, 1)

    if len(identity_ids) == 0:
        return {}

    cursor = connection.cursor()
    cursor.execute(sql, [MemoryStage.TESTED, tuple(identity_ids), started_since])
    return dict((r[0], r[1]) for r in cursor.fetchall())


import bibleverses.hooks
