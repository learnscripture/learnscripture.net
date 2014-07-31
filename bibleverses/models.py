from collections import defaultdict
import math
import re

from autoslug import AutoSlugField
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.utils import timezone
from django.utils.functional import cached_property
from jsonfield import JSONField 

# TextVersion and Verse are pseudo static, so make extensive use of caching.
# Other models won't benefit so much due to lots of writes and an increased
# risk if things go wrong.
import caching.base

from accounts import memorymodel
from bibleverses.fields import VectorField
from bibleverses.services import get_esv, search_esv
from learnscripture.datastructures import make_choices

import logging
logger = logging.getLogger(__name__)

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
                            ])


TextType = make_choices('TextType',
                        [(1, 'BIBLE', 'Bible'),
                         (2, 'CATECHISM', 'Catechism'),
                         ])

class TextVersionManager(caching.base.CachingManager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    def bibles(self):
        return self.get_query_set().filter(text_type=TextType.BIBLE)

    def catechisms(self):
        return self.get_query_set().filter(text_type=TextType.CATECHISM)


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

    @property
    def is_bible(self):
        return self.text_type == TextType.BIBLE

    @property
    def is_catechism(self):
        return self.text_type == TextType.CATECHISM

    class Meta:
        ordering = ['short_name']

    def __unicode__(self):
        return "%s (%s)" % (self.short_name, self.full_name)

    def natural_key(self):
        return (self.slug,)

    def get_verse_list(self, reference, max_length=MAX_VERSE_QUERY_SIZE):
        """
        Get ordered list of Verse objects for the given reference.
        (just one objects for most references).
        """
        return parse_ref(reference, self, max_length=max_length)

    def get_text_by_reference(self, reference):
        return ComboVerse(reference, self.get_verse_list(reference)).text

    def get_text_by_reference_bulk(self, reference_list):
        """
        Returns a dictionary of {ref:text} for each ref in reference_list. Bad
        references are silently discarded, and won't be in the return
        dictionary.
        """
        if not self.is_bible: return {}
        verse_dict = self.get_verses_by_reference_bulk(reference_list)
        return dict((ref, v.text) for (ref, v) in verse_dict.items())

    def get_verses_by_reference_bulk(self, reference_list):
        """
        Returns a dictionary of {ref:verse} for each ref in reference_list. Bad
        references are silently discarded, and won't be in the return
        dictionary.
        """
        if not self.is_bible: return {}
        # We try to do this efficiently, but it is hard for combo references. So
        # we do the easy ones the easy way:
        simple_verses = list(self.verse_set.filter(reference__in=reference_list,
                                                   missing=False,
                                                   ))
        v_dict = dict((v.reference, v) for v in simple_verses)
        # Now get the others:
        for ref in reference_list:
            if ref not in v_dict:
                try:
                    v_dict[ref] = ComboVerse(ref, self.get_verse_list(ref))
                except InvalidVerseReference:
                    pass
        ensure_text(v_dict.values())
        return v_dict

    def get_qapairs_by_reference_bulk(self, reference_list):
        if not self.is_catechism: return {}
        return {qapair.reference: qapair
                for qapair in self.qapairs.filter(reference__in=reference_list)}

    def get_qapair_by_reference(self, reference):
        if not self.is_catechism: return None
        return self.qapairs.get(reference=reference)

    def _get_reference_list(self, reference):
        if self.is_bible:
            return [v.reference for v in self.get_verse_list(reference)]
        else:
            return [reference]

    def _get_ordered_word_suggestion_data(self, reference):
        references = self._get_reference_list(reference)
        wsds = list(self.word_suggestion_data.filter(reference__in=references))
        # wsds might not be ordered correctly, we need to re-order
        retval = []
        for ref in references:
            for wsd in wsds:
                if wsd.reference == ref:
                    retval.append(wsd)
        return retval

    def get_suggestion_pairs_by_reference(self, reference):
        """
        For the given reference, returns a list of suggestion lists,
        one list for each word in the verse, where list is a sequence of
        (word, relative frequency) pairs.

        """
        wsds = self._get_ordered_word_suggestion_data(reference)
        # Now combine:
        retval = []
        for wsd in wsds:
            retval.extend(wsd.get_suggestion_pairs())
        return retval

    def get_suggestion_pairs_by_reference_bulk(self, reference_list):
        """
        Returns a dictionary of {ref:suggestions} for each ref in reference_list.
        'suggestions' is itself a list of suggestion dictionaries
        """
        # Do simple ones in bulk:
        simple_wsds = list(self.word_suggestion_data.filter(reference__in=reference_list))
        s_dict = dict((w.reference, w.get_suggestion_pairs()) for w in simple_wsds)
        # Others:
        for ref in reference_list:
            if ref not in s_dict:
                s_dict[ref] = self.get_suggestion_pairs_by_reference(ref)
        return s_dict

    def get_learners(self):
        # This doesn't have to be 100% accurate, so do an easier query - find
        # people who have learnt the first item
        return [uvs.for_identity.account
                for uvs in
                UserVerseStatus.objects
                .select_related('for_identity', 'for_identity__account')
                .filter(version=self,
                        text_order=1,
                        for_identity__account__isnull=False,
                        for_identity__account__is_active=True,
                        for_identity__account__is_hellbanned=False,
                        )]

    def record_word_mistakes(self, reference, mistake_list):
        # Takes a reference and a list of [word_number, wrong_word] pairs
        # and records the hit in the relevant WordSuggestionData
        #
        # Note that reference might be a combo e.g. Genesis 1:1-2 in which case
        # we need to make sure that word indexes in mistake_list are interpreted
        # correctly and get mapped back to correct WordSuggestionData
        wsds = self._get_ordered_word_suggestion_data(reference)
        list_sizes = [len(wsd.get_suggestion_pairs()) for wsd in wsds]

        # Find correct WordSuggestionData and word offset:
        mapped_mistakes = []
        for word_num, word in mistake_list:
            for i, s in enumerate(list_sizes):
                if word_num >= s:
                    word_num -= s
                else:
                    mapped_mistakes.append((i, word_num, word))
                    break

        # Group by WordSuggestionData
        mistake_d = defaultdict(list)
        for i, word_num, word in mapped_mistakes:
            mistake_d[i].append((word_num, word))

        for i, mistakes in mistake_d.items():
            wsd = wsds[i]
            for word_num, wrong_word in mistakes:
                wsd.record_mistake(word_num, wrong_word)
            wsd.save()


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

    @property
    def text(self):
        # Do this lazily, so that we can update .text in underlying Verse
        # objects if necessary.
        return ' '.join(v.text for v in self.verses)


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
    text = models.TextField(blank=True)
    text_tsv = VectorField()

    # De-normalised fields
    # Public facing fields are 1-indexed, others are 0-indexed.
    book_number = models.PositiveSmallIntegerField() # 0-indexed
    chapter_number = models.PositiveSmallIntegerField() # 1-indexed
    verse_number = models.PositiveSmallIntegerField()   # 1-indexed
    bible_verse_number = models.PositiveSmallIntegerField() # 0-indexed

    # This field is to cope with versions where a specific verse is entirely
    # empty e.g. John 5:4 in NET/ESV
    missing = models.BooleanField(default=False)

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

    def mark_missing(self):
        self.missing = True
        self.save()
        UserVerseStatus.objects.filter(version=self.version,
                                       reference=self.reference).delete()


class WordSuggestionData(models.Model):
    # All the suggestion data for a single verse/question
    # For efficiency, we avoid having millions of rows, because
    # we always need all the suggestions for a verse together.
    version = models.ForeignKey(TextVersion, related_name='word_suggestion_data')
    reference = models.CharField(max_length=100)
    hash = models.CharField(max_length=40) # SHA1 of text

    # Schema:
    # list of suggestions for each word, in order.
    # each suggestion consists of a list of tuples
    #  [(word, frequency, hits)]
    suggestions = JSONField()

    def get_suggestion_pairs(self):
        if not self.suggestions:
            return []
        # frequency is the suggested frequency based on
        # markov chains etc., normalised to 1.
        # hits is the number of times someone has chosen this word.
        # We use hits as a strong hint that this is a good word to use.

        return [[(word, frequency + hits)
                 for word, frequency, hits in suggestion]
                for suggestion in self.suggestions]

    def record_mistake(self, word_num, wrong_word):
        # Update hits for suggestion 'word' for word number 'word_num'
        s = self.suggestions
        s = [[(word, frequency, hits + (1 if word == wrong_word and word_num == i else 0))
              for word, frequency, hits in suggestion]
             for i, suggestion in enumerate(s)]
        self.suggestions = s

    class Meta:
        unique_together = [
            ('version', 'reference')
        ]

    def __repr__(self):
        return "<WordSuggestionData %s %s>" % (self.version.slug, self.reference)


class QAPair(models.Model):
    """
    A question/answer pair in a catechism.
    """
    catechism = models.ForeignKey(TextVersion, related_name='qapairs')
    # Reference is always 'Qn' where 'n' == order.  This means we are guaranteed
    # not to have clashes with Verse references, which is useful for the
    # UserVerseStatus models which can reference both.
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
    def visible_for_account(self, account):
        qs = self.public()
        if account is None or not account.is_hellbanned:
            qs = qs.exclude(created_by__is_hellbanned=True)

        if account is not None:
            qs = qs | account.verse_sets_created.all()

        return qs

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


    def search(self, verse_sets, query):
        # Does the query look like a Bible reference?
        reference = parse_as_bible_reference(query,
                                             allow_whole_book=False,
                                             allow_whole_chapter=False)
        if reference is not None:
            return verse_sets.filter(verse_choices__reference=reference)
        else:
            return verse_sets.filter(name__icontains=query)


class VerseSet(models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='name', unique=True)
    description = models.TextField(blank=True)
    additional_info = models.TextField(blank=True)
    set_type = models.PositiveSmallIntegerField(choices=VerseSetType.choice_list)

    public = models.BooleanField(default=False)
    breaks = models.TextField(default='', blank=True)

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

    def set_verse_choices(self, ref_list):
        existing_vcs = self.verse_choices.all()
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
            verse_choices = list(self.verse_choices.all())
            self.passage_id = verse_choices[0].reference + u' - ' + verse_choices[-1].reference
            self.save()


class VerseChoiceManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return super(VerseChoiceManager, self).get_query_set().order_by('set_order')


# Note that VerseChoice and Verse are not related, since we want a VerseChoice
# to be independent of Bible version.
class VerseChoice(models.Model):
    reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, related_name='verse_choices')
    set_order = models.PositiveSmallIntegerField(default=0)

    objects = VerseChoiceManager()

    class Meta:
        unique_together = [('verse_set', 'reference')]

    def __unicode__(self):
        return self.reference

    def __repr__(self):
        return u'<VerseChoice %s>' % self


class UserVerseStatus(models.Model):
    """
    Tracks the user's progress for a verse or QAPair
    """
    # It actually tracks the progress for a reference and Version.  This
    # implicitly allows it to track progress separately for different versions
    # and for the same verse in different verse sets.  In some cases this is
    # useful (for learning a passage, you might be learning a different version
    # to normal), but usually it is confusing, so business logic limits how much
    # this can happen.

    # By making reference a CharField instead of a tighter DB constraint, we can
    # handle:
    # - UserVerseStatuses that don't correspond to a Verse object, because
    #   they span a few verses.
    # - the case of VerseChoices or VerseSets being deleted,
    # - UVSs that are not attached to VerseSets at all.
    # - QAPairs and Verses from the same model
    #
    # Since references don't change we can handle the denormalisation easily.

    for_identity = models.ForeignKey('accounts.Identity', related_name='verse_statuses')
    reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, null=True, blank=True,
                                  on_delete=models.SET_NULL)
    text_order = models.PositiveSmallIntegerField() # order of this item within associate TextVersion
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

    @cached_property
    def question(self):
        return self.version.get_qapair_by_reference(self.reference).question

    @cached_property
    def title(self):
        return self.reference + \
            ('' if self.version.is_bible else '. ' + self.question)

    @cached_property
    def short_title(self):
        if self.version.is_bible:
            return self.reference
        else:
            return self.version.short_name + " - " + self.reference

    @cached_property
    def item_name(self):
        return 'verse' if self.version.is_bible else 'question'

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

    # This will be overwritten by get_verse_statuses_bulk
    @cached_property
    def suggestion_pairs(self):
        return self.version.get_suggestion_pairs_by_reference(self.reference)

    def __unicode__(self):
        return u"%s, %s" % (self.reference, self.version.slug)

    def __repr__(self):
        return u'<UserVerseStatus %s>' % self

    class Meta:
        unique_together = [('for_identity', 'verse_set', 'reference', 'version')]
        verbose_name_plural = "User verse statuses"


WORD_RE = re.compile('[0-9a-zA-Z]')

def is_punctuation(text):
    return not WORD_RE.search(text)


def split_into_words(text, fix_punctuation_whitespace=True):
    # This logic is reproduced client side in learn.js :: countWords
    # in order to display target.

    # We need to cope with things like Gen 3:22
    #    and live forever--"'
    # and Gen 1:16
    #    And God made the two great lights--the greater light
    #
    # and when -- appears with punctuation on one side, we don't
    # want this to end up on its own. Also, text with a single
    # hyphen surrounding by whitespace needs to be handled too.
    l = text.replace('--', ' -- ').strip().split()
    if fix_punctuation_whitespace:
        # Merge punctuation only items with item to left.
        l = merge_punctuation_items_right(merge_punctuation_items_left(l))

    return l


def merge_punctuation_items_left(words):
    retval = []
    for item in words:
        if is_punctuation(item) and len(retval) > 0:
            retval[-1] += item
        else:
            retval.append(item)
    return retval

def merge_punctuation_items_right(words):
    retval = []
    for item in words[::-1]:
        if is_punctuation(item) and len(retval) > 0:
            retval[-1] = item + retval[-1]
        else:
            retval.append(item)
    return retval[::-1]

def count_words(text):
    return len(split_into_words(text))


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
            retval = list(version.verse_set
                          .filter(book_number=book_number,
                                  chapter_number=chapter_number,
                                  missing=False)
                          .order_by('bible_verse_number')
                      )
        else:
            retval = Reference(book, chapter_number, None)
    else:
        parts = reference.rsplit(u'-', 1)
        if len(parts) == 1:
            # e.g. Genesis 1:1
            if return_verses:
                retval = list(version.verse_set.filter(reference=reference,
                                                       missing=False))
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
                #
                # We don't do 'missing=False' filter here, because we want to be
                # able to do things like 'John 5:3-4' even if 'John 5:4' is
                # missing in the current version. We just miss out the missing
                # verses when creating the list.
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
                                                       bible_verse_number__lte=verse_end.bible_verse_number,
                                                       missing=False))
            else:
                retval = (Reference(book, start_chapter, start_verse),
                          Reference(book, end_chapter, end_verse))

    if return_verses:
        if len(retval) == 0:
            raise InvalidVerseReference(u"No verses matched '%s'." % reference)

        if len(retval) > max_length:
            raise InvalidVerseReference(u"References that span more than %d verses are not allowed in this context." % max_length)

        # Ensure back references to version are set, so we don't need extra DB lookup
        for v in retval:
            v.version = version
        # Ensure verse.text is set
        ensure_text(retval)

    return retval


retrieve_version_services = {
    'ESV': get_esv,
}

def ensure_text(verses):
    refs_missing_text = defaultdict(list) # divided by version
    verse_dict = {}
    for v in verses:
        if v.text == '' and not v.missing:
            refs_missing_text[v.version.short_name].append(v.reference)
            verse_dict[v.version.short_name, v.reference] = v

    # Version specific stuff:
    for short_name, service in retrieve_version_services.items():
        missing = refs_missing_text[short_name]
        if missing:
            for ref, text in service(missing):
                v = verse_dict[short_name, ref]
                v.text = text
                v.save()

    for v in verses:
        if v.text == '' and not v.missing:
            logger.warn("Marking %s %s as missing", short_name, v.reference)
            v.missing = True
            v.save()


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


version_specific_searches = {
    'ESV': search_esv,
}


def parse_as_bible_reference(query, allow_whole_book=True, allow_whole_chapter=True):
    """
    Returns a normalised Bible reference if the query looks like one,
    or None otherwise.

    Pass allow_whole_book=False if queries that are just book names should be rejected.
    Pass allow_whole_chapter=False if queries that are whole chapters should be rejected
    """
    query = query.lower().strip()

    bible_ref_re = (
        r'^(?:(?:1|2|3)\s*)?[^\d]*'  # book name
        r'\s+'                       # space
        r'(\d+)'                     # chapter
        r'\s*('                      # optionally:
            r'(v|:|\.)'              #    v or : or .
            r'\s*\d+'                #    and start verse number
            r'('                     #    and optionally:
              r'\s*-\s*\d+'          #        end verse/next chapter num
              r'(\s*(v|:|\.)'        #        and optionally end verse
               r'\s*\d+)?'
            r')?'
        r')?'
        r'$'
        )

    m = re.match(bible_ref_re, query)
    if m:
        if not allow_whole_chapter and m.groups()[1] is None:
            return None
        else:
            return normalise_reference(query)
    else:
        if allow_whole_book and query in BIBLE_BOOK_ABBREVIATIONS:
            return normalise_reference(query)


    return None


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

    reference = parse_as_bible_reference(query, allow_whole_book=not allow_searches)
    if reference is not None:
        return [ComboVerse(reference, parse_ref(reference, version, max_length=max_length))]

    if not allow_searches:
        raise InvalidVerseReference("Verse reference not recognised")

    # Do a search:
    if version.short_name in version_specific_searches:
        return version_specific_searches[version.short_name](version, query)

    results = Verse.objects.text_search(query, version, limit=11)
    return [ComboVerse(r.reference, [r]) for r in results]


def get_whole_book(book_name, version):
    retval = ComboVerse(book_name, version.verse_set.filter(book_number=BIBLE_BOOKS_DICT[book_name],
                                                            missing=False))
    ensure_text(retval.verses)
    return retval


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
    used_parts = 1
    if len(parts) > 1:
        for p in range(1, len(parts)):
            if not re.search(u'\d', parts[p]):
                book_name = book_name + u" " + parts[p]
                used_parts += 1
            else:
                break

    if book_name in BIBLE_BOOK_ABBREVIATIONS:
        remainder = u" ".join(parts[used_parts:])
        return (BIBLE_BOOK_ABBREVIATIONS[book_name] + u" " + remainder).strip()
    else:
        return None


from bibleverses import hooks
