# -*- coding: utf-8 -*-
import logging
import math
import random
from collections import defaultdict

from autoslug import AutoSlugField
from django.db import connection, models
from django.db.models import F, Func, Value
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from jsonfield import JSONField

from accounts import memorymodel
from learnscripture.datastructures import make_choices
from learnscripture.utils.iterators import intersperse

from .books import get_bible_book_name, get_bible_book_number
from .fields import VectorField
from .languages import DEFAULT_LANGUAGE, LANGUAGE_CHOICES, LANGUAGE_CODE_EN, LANGUAGE_CODE_TR, normalize_reference_input
from .parsing import (InvalidVerseReference, ParsedReference, parse_break_list, parse_unvalidated_localized_reference,
                      parse_validated_localized_reference)
from .services import get_fetch_service, get_search_service
from .textutils import split_into_words

logger = logging.getLogger(__name__)


# Psalm 119 is 176 verses
MAX_VERSE_QUERY_SIZE = 200
MAX_VERSES_FOR_SINGLE_CHOICE = 4  # See also choose.js


# Also defined in learn.js
VerseSetType = make_choices('VerseSetType',
                            [(1, 'SELECTION', 'Selection'),
                             (2, 'PASSAGE', 'Passage'),
                             ])

StageType = make_choices('StageType',
                         [(1, 'READ', 'read'),
                          (2, 'RECALL_INITIAL', 'recall from initials'),
                          (3, 'RECALL_MISSING', 'recall when missing'),
                          (4, 'TEST', 'test'),  # Also used in learn.js
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


class TextVersionManager(models.Manager):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    def bibles(self):
        return self.get_queryset().filter(text_type=TextType.BIBLE)

    def catechisms(self):
        return self.get_queryset().filter(text_type=TextType.CATECHISM)


class TextVersion(models.Model):
    short_name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255, unique=True)
    url = models.URLField(default="", blank=True)
    text_type = models.PositiveSmallIntegerField(choices=TextType.choice_list,
                                                 default=TextType.BIBLE)
    language_code = models.CharField(max_length=2, blank=False,
                                     choices=LANGUAGE_CHOICES,
                                     default=DEFAULT_LANGUAGE.code)
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

    def __str__(self):
        return "%s (%s)" % (self.short_name, self.full_name)

    def natural_key(self):
        return (self.slug,)

    def get_verse_list(self, localized_reference, max_length=MAX_VERSE_QUERY_SIZE):
        """
        Get ordered list of Verse objects for the given localized reference.
        (just one object for most references).
        """
        return fetch_localized_reference(
            self,
            self.language_code,
            localized_reference,
            max_length=max_length)

    def get_text_by_localized_reference(self, localized_reference):
        return ComboVerse(localized_reference, self.get_verse_list(localized_reference)).text

    def get_text_by_localized_reference_bulk(self, localized_reference_list):
        """
        Returns a dictionary of {localized_ref:text} for each ref in localized_reference_list. Bad
        references are silently discarded, and won't be in the return
        dictionary.
        """
        if not self.is_bible:
            return {}
        verse_dict = self.get_verses_by_localized_reference_bulk(localized_reference_list)
        return dict((r, v.text) for (r, v) in verse_dict.items())

    def get_verses_by_localized_reference_bulk(self, localized_reference_list, fetch_text=True):
        """
        Returns a dictionary of {localized_ref:verse} for each ref in localized_reference_list. Bad
        references are silently discarded, and won't be in the return
        dictionary.
        """
        if not self.is_bible:
            return {}
        return fetch_localized_reference_bulk(
            self, self.language_code, localized_reference_list,
            fetch_text=fetch_text)

    def get_qapairs_by_localized_reference_bulk(self, localized_reference_list):
        if not self.is_catechism:
            return {}
        return {qapair.localized_reference: qapair
                for qapair in self.qapairs.filter(localized_reference__in=localized_reference_list)}

    def get_qapair_by_localized_reference(self, localized_reference):
        if not self.is_catechism:
            return None
        return self.qapairs.get(localized_reference=localized_reference)

    def get_item_by_localized_reference(self, localized_reference):
        if self.is_bible:
            return self.verse_set.get(localized_reference=localized_reference)
        elif self.is_catechism:
            return self.get_qapair_by_localized_reference(localized_reference)

    def get_localized_reference_list(self, localized_reference):
        if self.is_bible:
            return [v.localized_reference for v in self.get_verse_list(localized_reference)]
        else:
            return [localized_reference]

    def get_suggestions_by_localized_reference(self, localized_reference):
        """
        For the given localized reference, returns a list of suggestion lists,
        one list for each word in the verse
        """
        from .suggestions.modelapi import get_word_suggestions_by_localized_reference
        return get_word_suggestions_by_localized_reference(self, localized_reference)

    def get_suggestions_by_localized_reference_bulk(self, localized_reference_list):
        """
        Returns a dictionary of {localized_reference:suggestions} for each ref in localized_reference_list.
        'suggestions' is itself a list of suggestion dictionaries
        """
        from .suggestions.modelapi import get_word_suggestions_by_localized_reference_bulk
        return get_word_suggestions_by_localized_reference_bulk(self, localized_reference_list)

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

    # Simulate FK to WordSuggestionData
    @property
    def word_suggestion_data(self):
        from .suggestions.modelapi import word_suggestion_data_qs_for_version
        return word_suggestion_data_qs_for_version(self)

    @property
    def db_based_searching(self):
        return get_search_service(self.slug) is None

    def update_text_search(self, verses_qs):
        verses_qs.update(text_tsv=Func(
            Value(POSTGRES_SEARCH_CONFIGURATIONS[self.language_code]),
            F('text_saved'),
            function='to_tsvector'))


class ComboVerse(object):
    """
    Wrapper needed when we want a combination of verses to appear as a single
    verse.
    """
    def __init__(self, localized_reference, verse_list):
        self.localized_reference = localized_reference
        self.book_name = verse_list[0].book_name
        self.chapter_number = verse_list[0].chapter_number
        self.first_verse_number = verse_list[0].first_verse_number
        self.last_verse_number = verse_list[-1].last_verse_number
        self.bible_verse_number = verse_list[0].bible_verse_number
        self.verses = verse_list

    @property
    def text(self):
        # Do this lazily, so that we can update .text_saved in underlying Verse
        # objects if necessary.
        return ' '.join(v.text for v in self.verses)


class VerseSearchResult(ComboVerse):
    def __init__(self, localized_reference, verse_list,
                 parsed_ref=None,
                 from_reference=None):
        super().__init__(localized_reference, verse_list)
        self.from_reference = from_reference
        self.parsed_ref = parsed_ref


SEARCH_OPERATORS = set(["&", "|", "@@", "@@@", "||", "&&", "!!", "@>", "<@", ":", "\\"])
SEARCH_CHARS = set("".join(list(SEARCH_OPERATORS)))


# See '\dF' command in psql for list of available builtin configurations.
POSTGRES_SEARCH_CONFIGURATIONS = {
    LANGUAGE_CODE_EN: 'english',
    LANGUAGE_CODE_TR: 'turkish',
}


class VerseManager(models.Manager):

    def get_by_natural_key(self, version_slug, localized_reference):
        return self.get(version__slug=version_slug, localized_reference=localized_reference)

    def text_search(self, query, version, limit=10):
        # First remove anything recognized by postgres as an operator.
        for s in SEARCH_CHARS:
            query = query.replace(s, " ")
        words = query.split(' ')
        words = [w for w in words
                 if (w and w not in SEARCH_OPERATORS)]
        # Do an 'AND' on all terms.
        word_params = list(intersperse(words, ' & '))
        search_clause = ' || ' .join(['%s'] * len(word_params))
        search_config = POSTGRES_SEARCH_CONFIGURATIONS[version.language_code]
        return models.Manager.raw(self, """
          SELECT id, version_id, localized_reference, text_saved,
                 ts_headline(text_saved, query, 'StartSel = **, StopSel = **, HighlightAll=TRUE') as highlighted_text,
                 book_number, chapter_number, first_verse_number, last_verse_number,
                 bible_verse_number, ts_rank(text_tsv, query) as rank
          FROM bibleverses_verse, to_tsquery(%s, """ + search_clause + """) query
          WHERE
             query @@ text_tsv
             AND version_id = %s
          ORDER BY rank DESC
          LIMIT %s;
""", [search_config] + word_params + [version.id, limit])


class Verse(models.Model):
    version = models.ForeignKey(TextVersion, on_delete=models.CASCADE)
    localized_reference = models.CharField(max_length=100)
    # 'text_saved' is for data stored, as opposed to 'text' which might retrieve
    # from a service. Also, 'text_saved' is sometimes set without saving to the
    # DB, just so that 'text' can find it.
    text_saved = models.TextField(blank=True)
    text_tsv = VectorField()
    text_fetched_at = models.DateTimeField(null=True, blank=True)

    # De-normalized fields
    # Public facing fields are 1-indexed, others are 0-indexed.
    book_number = models.PositiveSmallIntegerField()  # 0-indexed
    chapter_number = models.PositiveSmallIntegerField()  # 1-indexed
    first_verse_number = models.PositiveSmallIntegerField()  # 1-indexed
    # Usually last_verse_number is equal to first_verse_number
    last_verse_number = models.PositiveSmallIntegerField()  # 1-indexed

    # Position within the Bible:
    bible_verse_number = models.PositiveSmallIntegerField()  # 0-indexed

    # This field is to cope with versions where a specific verse is entirely
    # empty e.g. John 5:4 in NET/ESV
    missing = models.BooleanField(default=False)

    merged_into = models.ForeignKey("self", on_delete=models.CASCADE,
                                    blank=True, null=True)

    objects = VerseManager()

    @property
    def text(self):
        if self.text_saved == "" and not self.missing:
            logger.warning("Reached ensure_text call from Verse.text, for %s %s",
                           self.version.slug, self.localized_reference)
            ensure_text([self])
        return self.text_saved

    @cached_property
    def display_verse_number(self):
        if self.last_verse_number == self.first_verse_number:
            return str(self.first_verse_number)
        else:
            return "{0}-{1}".format(self.first_verse_number, self.last_verse_number)

    @property
    def book_name(self):
        return get_bible_book_name(self.version.language_code, self.book_number)

    def natural_key(self):
        return (self.version.slug, self.localized_reference)

    def __str__(self):
        return "%s (%s)" % (self.localized_reference, self.version.short_name)

    def __repr__(self):
        return '<Verse %s>' % self

    class Meta:
        unique_together = [
            ('bible_verse_number', 'version'),
            ('localized_reference', 'version'),
        ]
        ordering = ('bible_verse_number',)

    def mark_missing(self):
        self.missing = True
        self.save()
        UserVerseStatus.objects.filter(version=self.version,
                                       localized_reference=self.localized_reference).delete()

    @property
    def suggestion_text(self):
        """
        Text needed by suggestions code
        """
        return self.text

    @property
    def text_version(self):
        """
        The related TextVersion object
        """
        return self.version


SUGGESTION_COUNT = 10


class WordSuggestionData(models.Model):
    # All the suggestion data for a single verse/question
    # For efficiency, we avoid having millions of rows, because
    # we always need all the suggestions for a verse together.

    # For practical reasons, this table is stored in a separate DB, so it has no
    # explicit FKs to the main DB.
    version_slug = models.CharField(max_length=20, default='')
    localized_reference = models.CharField(max_length=100)
    hash = models.CharField(max_length=40)  # SHA1 of text

    # Schema: list of suggestions for each word, in order. each suggestion
    # consists of a list of words in decreasing order of fitness.
    # So we have
    # [[suggestion_1_for_word_1, s_2_for_w_1,...],[s_1_for_w_2, s_2_for_w_2]]
    suggestions = JSONField()

    def get_suggestions(self):
        if not self.suggestions:
            return []
        # We could do some of this client side, but we save on bandwidth by
        # returning only a selection of the words, not all the data.

        retval = []

        for word_suggestions in self.suggestions:
            # Assign a frequency between 0.5 and 1.0 for each word
            # (lower than 0.5 means they end up not being seen at all
            #  in practice)
            pairs = [(word, 1.0 - i * 0.5 / len(word_suggestions))
                     for i, word in enumerate(word_suggestions)]

            # Make a random selection, weighted according to frequency
            chosen = set()
            available = pairs[:]
            while len(chosen) < SUGGESTION_COUNT and len(available) > 0:
                if len(available) == 1:
                    # No point doing random
                    picked = available[0][0]
                else:
                    # Weighting:
                    threshold = random.random()  # 0..1
                    possible = [word for word, freq in available if freq >= threshold]
                    if not possible:
                        continue
                    # Pick one
                    picked = random.choice(possible)
                chosen.add(picked)
                available = [(word, freq) for word, freq in available if word != picked]

            retval.append(sorted(chosen))
        return retval

    class Meta:
        unique_together = [
            ('version_slug', 'localized_reference')
        ]

    def __repr__(self):
        return "<WordSuggestionData %s %s>" % (self.version_slug, self.localized_reference)


class QAPairManager(models.Manager):

    def get_by_natural_key(self, catechism_slug, localized_reference):
        return self.get(catechism__slug=catechism_slug, localized_reference=localized_reference)


class QAPair(models.Model):
    """
    A question/answer pair in a catechism.
    """
    catechism = models.ForeignKey(TextVersion, on_delete=models.CASCADE, related_name='qapairs')
    # localized_reference is always 'Qn' where 'n' == order. (Apart from where
    # we have question numbers like '2a').
    # localized_reference is referred to by UserVerseStatus
    localized_reference = models.CharField(max_length=100)
    question = models.TextField()
    answer = models.TextField()
    order = models.PositiveSmallIntegerField()

    objects = QAPairManager()

    class Meta:
        unique_together = [('catechism', 'order'),
                           ('catechism', 'localized_reference')]

        verbose_name = "QA pair"
        ordering = ['order']

    def __str__(self):
        return self.localized_reference + " " + self.question

    def natural_key(self):
        return (self.catechism.slug, self.localized_reference)

    @property
    def suggestion_text(self):
        """
        Text needed by suggestions code
        """
        return self.answer

    @property
    def text_version(self):
        """
        The related TextVersion object
        """
        return self.catechism


class VerseSetManager(models.Manager):
    def visible_for_account(self, account):
        qs = self.public()
        if account is None or not account.is_hellbanned:
            qs = qs.exclude(created_by__is_hellbanned=True)

        if account is not None:
            qs = qs | account.verse_sets_created.all()

        return qs

    def public(self):
        return self.get_queryset().filter(public=True)

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

    def search(self, language_code, verse_sets, query):
        # Does the query look like a Bible reference?
        try:
            parsed_ref = parse_unvalidated_localized_reference(
                language_code,
                query,
                allow_whole_book=False,
                allow_whole_chapter=False)
        except InvalidVerseReference:
            return verse_sets.none()
        if parsed_ref is not None:
            return verse_sets.filter(verse_choices__localized_reference=parsed_ref.canonical_form())
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
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE,
                                   related_name='verse_sets_created')

    # Essentially denormalized field, to make it quick to check for duplicate
    # passage sets:
    passage_id = models.CharField(max_length=203,  # 100 for reference * 2 + 3 for ' - '
                                  default="")

    objects = VerseSetManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('view_verse_set', kwargs=dict(slug=self.slug))

    @property
    def is_passage(self):
        return self.set_type == VerseSetType.PASSAGE

    @property
    def is_selection(self):
        return self.set_type == VerseSetType.SELECTION

    @property
    def breaks_formatted(self):
        return self.breaks.replace(",", ", ")

    def set_verse_choices(self, localized_reference_list):
        existing_vcs = self.verse_choices.all()
        existing_vcs_dict = dict((vc.localized_reference, vc) for vc in existing_vcs)
        old_vcs = set(existing_vcs)
        for i, ref in enumerate(localized_reference_list):  # preserve order
            dirty = False
            if ref in existing_vcs_dict:
                vc = existing_vcs_dict[ref]
                if vc.set_order != i:
                    vc.set_order = i
                    dirty = True
                old_vcs.remove(vc)
            else:
                vc = VerseChoice(verse_set=self,
                                 localized_reference=ref,
                                 set_order=i)
                dirty = True
            if dirty:
                vc.save()

        # Delete unused VerseChoice objects.
        for vc in old_vcs:
            vc.delete()

        self.update_passage_id()

    def update_passage_id(self):
        if self.is_passage:
            verse_choices = list(self.verse_choices.all())
            self.passage_id = verse_choices[0].localized_reference + ' - ' + verse_choices[-1].localized_reference
            self.save()


class VerseChoiceManager(models.Manager):

    def get_queryset(self):
        return super(VerseChoiceManager, self).get_queryset().order_by('set_order')


# Note that VerseChoice and Verse are not related, since we want a VerseChoice
# to be independent of Bible version.
class VerseChoice(models.Model):
    localized_reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, on_delete=models.CASCADE,
                                  related_name='verse_choices')
    set_order = models.PositiveSmallIntegerField(default=0)

    objects = VerseChoiceManager()

    class Meta:
        unique_together = [('verse_set', 'localized_reference')]
        base_manager_name = 'objects'

    def __str__(self):
        return self.localized_reference

    def __repr__(self):
        return '<VerseChoice %s>' % self


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

    # By making localized_reference a CharField instead of a tighter DB constraint, we can
    # handle:
    # - UserVerseStatuses that don't correspond to a Verse object, because
    #   they span a few verses.
    # - the case of VerseChoices or VerseSets being deleted,
    # - UVSs that are not attached to VerseSets at all.
    # - QAPairs and Verses being related to the same model
    #
    # Since references don't change we can handle the denormalisation easily.

    for_identity = models.ForeignKey('accounts.Identity', on_delete=models.CASCADE,
                                     related_name='verse_statuses')
    localized_reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, null=True, blank=True,
                                  on_delete=models.SET_NULL)
    text_order = models.PositiveSmallIntegerField()  # order of this item within associate TextVersion
    version = models.ForeignKey(TextVersion, on_delete=models.CASCADE)
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
        return self.version.get_text_by_localized_reference(self.localized_reference)

    @cached_property
    def question(self):
        return self.version.get_qapair_by_localized_reference(self.localized_reference).question

    @cached_property
    def answer(self):
        return self.version.get_qapair_by_localized_reference(self.localized_reference).answer

    @cached_property
    def title(self):
        return self.localized_reference + \
            ('' if self.version.is_bible else '. ' + self.question)

    # This will be overwritten by get_verse_statuses_bulk
    @cached_property
    def scoring_text(self):
        return self.text if self.version.is_bible else self.answer

    @property
    def scoring_text_words(self):
        return split_into_words(self.scoring_text)

    @cached_property
    def short_title(self):
        if self.version.is_bible:
            return self.localized_reference
        else:
            return self.version.short_name + " - " + self.localized_reference

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
        Returns the strength normalized to a 0 to 10 scale for presentation in UI.
        """
        return min(10, int(math.floor((self.strength / memorymodel.LEARNT) * 10)))

    @cached_property
    def passage_localized_reference(self):
        """
        Returns the localized reference for the whole passage this UVS belongs to.
        """
        if not self.is_in_passage():
            return None
        verse_choices = self.set_verse_choices
        return pretty_passage_ref(
            self.version.language_code,
            verse_choices[0].localized_reference,
            verse_choices[-1].localized_reference)

    @cached_property
    def set_verse_choices(self):
        return list(self.verse_set.verse_choices.all())

    @cached_property
    def section_localized_reference(self):
        """
        Returns the localized reference for the section in the passage this UVS belongs to.
        """
        if not self.is_in_passage():
            return None

        section = self.get_section_verse_choices()
        if section is not None:
            return pretty_passage_ref(
                self.version.language_code,
                section[0].localized_reference,
                section[-1].localized_reference)
        return None  # Shouldn't get here

    def get_section_verse_choices(self):
        # Split verse set into sections
        sections = get_passage_sections(self.version.language_code,
                                        self.set_verse_choices, self.verse_set.breaks)

        # Now we've got to find which one we are in:
        for section in sections:
            for vc in section:
                if vc.localized_reference == self.localized_reference:
                    return section

    # This will be overwritten by get_verse_statuses_bulk
    @cached_property
    def suggestions(self):
        return self.version.get_suggestions_by_localized_reference(self.localized_reference)

    def __str__(self):
        return "%s, %s" % (self.localized_reference, self.version.slug)

    def __repr__(self):
        return '<UserVerseStatus %s>' % self

    class Meta:
        unique_together = [('for_identity', 'verse_set', 'localized_reference', 'version')]
        verbose_name_plural = "User verse statuses"


#  ---- Verse fetching ----
#
# This is significantly complicated by several factors:
#
# * We sometimes often want to fetch in bulk - for example,
#   when starting a learning session for a set of UserVerseStatuses
#   and sometimes just want a single 'thing'. This results in many functions
#   having two versions, bulk and non-bulk for efficiency.
#
# * We sometimes want to parse verse references loosely (e.g. from non-canonical
#   user entered data)
#
# * We need to handle:
#   - Combo verses (e.g. when a user chooses to learn several verses
#     together as single verse e.g. Ephesians 2:8-9)
#   - Passages - we want to retrieve all of "John 1:1-15", to be displayed in a list
#   - Merged verses - where the underlying Bible translation has put several
#     verses together e.g. TCL02 Romalılar 3:25-26.
#   - Missing verses - where the translation doesn't have a certain verse.
#
# * We many need to tolerate some incorrectness in requested references e.g. not
#   accounting for merged verses in underlying translation.
#
# * For some TextVersions we don't store the whole text locally due to license
#   agreements. We only have a limited local cache and must get the remainder
#   from a service (but avoid doing so wherever possible)
#
# * And then the combination of all these (e.g. merged verses and combo verses)
#   with the edge cases, combined with trying to get data efficiently with the
#   minimum of DB queries.

def fetch_localized_reference(version,
                              language_code,
                              localized_reference,
                              max_length=MAX_VERSE_QUERY_SIZE):
    parsed_ref = parse_validated_localized_reference(language_code, localized_reference)
    return fetch_parsed_reference(version, parsed_ref, max_length=max_length)


def fetch_parsed_reference(version, parsed_ref, max_length=MAX_VERSE_QUERY_SIZE):
    """
    Fetch the ParsedReference from the DB, return
    as a list of Verse objects.

    If references that are incorrect due to merged verses will be automatically
    corrected.

    If otherwise incorrect, InvalidVerseReference will be raised
    """
    # TODO - for some uses, it is probably bad that we autocorrect merged
    # references, because then things might not line up later. We should throw
    # an exception perhaps? Or ensure that when we create UserVerseStatus
    # objects we always correct the refs first, not rely on correcting later.
    if parsed_ref.is_whole_chapter():
        retval = list(version.verse_set
                      .filter(book_number=parsed_ref.book_number,
                              chapter_number=parsed_ref.start_chapter,
                              missing=False)
                      .order_by('bible_verse_number')
                      )
    elif parsed_ref.is_single_verse():
        ref = parsed_ref.canonical_form()
        verse_d = fetch_by_localized_reference_simple_bulk(version, [ref])
        if ref in verse_d:
            retval = [verse_d[ref]]
        else:
            retval = []
    else:
        ref_start = parsed_ref.get_start().canonical_form()
        ref_end = parsed_ref.get_end().canonical_form()
        # Try to get results in just two queries
        #
        # We don't do 'missing=False' filter here, because we want to be
        # able to do things like 'John 5:3-4' even if 'John 5:4' is
        # missing in the current version.
        # We also need to handle merged verses, which are marked as 'missing=True'.
        # We just miss out the missing verses when creating the list.
        vs = version.verse_set.filter(localized_reference__in=[ref_start, ref_end])
        try:
            verse_start = [v for v in vs if v.localized_reference == ref_start][0]
        except IndexError:
            raise InvalidVerseReference("Can't find  '%s'" % ref_start)
        try:
            verse_end = [v for v in vs if v.localized_reference == ref_end][0]
        except IndexError:
            raise InvalidVerseReference("Can't find  '%s'" % ref_end)

        if verse_end.bible_verse_number < verse_start.bible_verse_number:
            raise InvalidVerseReference("%s and %s are not in ascending order." % (ref_start, ref_end))

        items = (version.verse_set
                 .filter(bible_verse_number__gte=verse_start.bible_verse_number,
                         bible_verse_number__lte=verse_end.bible_verse_number)
                 .select_related('merged_into'))
        retval = []
        used_ids = set()
        # Handle merged verses
        for item in items:
            if item.merged_into is not None:
                real = item.merged_into
            elif item.missing:
                real = None
            else:
                real = item
            if real is not None and real.id not in used_ids:
                retval.append(real)
                used_ids.add(real.id)

    if len(retval) == 0:
        raise InvalidVerseReference("No verses matched '%s'." % parsed_ref.canonical_form())

    if len(retval) > max_length:
        raise InvalidVerseReference("References that span more than %d verses are not allowed in this context." % max_length)

    # Ensure back references to version are set, so we don't need extra DB lookup
    for v in retval:
        v.version = version
    # Ensure verse.text_saved is set
    ensure_text(retval)

    return retval


def fetch_localized_reference_bulk(version, language_code,
                                   localized_reference_list,
                                   fetch_text=True):
    """
    Returns a dictionary {ref: Verse or ComboVerse} for refs matching the request references.
    Missing references will be silently discarded.
    Incorrect refs due to merged verses will be corrected.
    """
    # We try to do this efficiently, but it is hard for combo references. So
    # we do the easy ones the easy way:
    v_dict = fetch_by_localized_reference_simple_bulk(version, localized_reference_list)
    # Now get the others:
    for localized_ref in localized_reference_list:
        if localized_ref not in v_dict:
            try:
                vl = fetch_localized_reference(version,
                                               language_code,
                                               localized_ref)
                # In theory, localized_reference_list should already have been
                # corrected for merged verses. But if it has not been, this will
                # correct it so that the ComboVerse has the correct reference.
                normalized_localized_ref = normalized_verse_list_ref(language_code, vl)
                v_dict[localized_ref] = ComboVerse(normalized_localized_ref,
                                                   vl)
            except InvalidVerseReference:
                pass
    if fetch_text:
        ensure_text(v_dict.values())
    return v_dict


def fetch_by_localized_reference_simple_bulk(version, localized_reference_list):
    """
    Returns a dictionary {ref: Verse} for refs matching the request references.
    It may not be a complete.
    Incorrect refs due to merged verses will be corrected.
    """
    # Allow missing refs, because we need to find merged ones
    l = (version.verse_set
         .filter(localized_reference__in=localized_reference_list)
         .select_related('merged_into'))
    verse_d = {v.localized_reference: v for v in l}

    # Replace verses with the corrected one, as defined by 'merged_into' FK
    for ref in localized_reference_list:
        if ref in verse_d:
            v = verse_d[ref]
            if v.merged_into is not None:
                verse_d[ref] = v.merged_into
            elif v.missing:
                del verse_d[ref]
    return verse_d


def ensure_text(verses):
    """
    Call ensure_text for a group of Verse objects to ensure that the text has
    been fetched if necessary.
    """
    # This fetches the data as necessary, saving it or priming the cache.
    # It is much more efficient to call it on all verses needed up front,
    # due to the way we can batch requests to external services that get
    # the data.

    # Get the complete list:
    verses_to_check = []

    def add_verses(v_list):
        for v in v_list:
            if hasattr(v, 'verses'):
                # ComboVerse - add the subcomponents,
                # not the main one.
                add_verses(v.verses)
            else:
                verses_to_check.append(v)

    add_verses(verses)

    # Group into versions
    refs_missing_text = defaultdict(list)  # divided by version
    verse_dict = {}

    for v in verses_to_check:
        if v.text_saved == '' and not v.missing:
            refs_missing_text[v.version.slug].append(v.localized_reference)
            verse_dict[v.version.slug, v.localized_reference] = v

    # Now do the fetches
    for version_slug, missing_refs in refs_missing_text.items():
        fetcher = get_fetch_service(version_slug)
        if fetcher is None:
            continue  # no service for retrieving data

        for ref, text in fetcher(missing_refs):
            v = verse_dict[version_slug, ref]
            v.text_saved = text
            v.text_fetched_at = timezone.now()
            v.save()

    # Check that we fixed everything
    for v in verses_to_check:
        if v.text_saved == '' and not v.missing:
            logger.warning("Marking %s %s as missing", v.version.slug, v.localized_reference)
            v.missing = True
            v.save()


def pretty_passage_ref(language_code, start_ref, end_ref):
    return ParsedReference.from_start_and_end(
        parse_validated_localized_reference(language_code, start_ref),
        parse_validated_localized_reference(language_code, end_ref)
    ).canonical_form()


def normalized_verse_list_ref(language_code, verse_list):
    if len(verse_list) == 1:
        return verse_list[0].localized_reference
    else:
        return ParsedReference.from_start_and_end(
            parse_validated_localized_reference(language_code, verse_list[0].localized_reference),
            parse_validated_localized_reference(language_code, verse_list[-1].localized_reference)
        ).canonical_form()


def get_passage_sections(language_code, verse_list, breaks):
    """
    Given a list of objects with a correct 'localized_reference' attribute, and a comma
    separated list of 'break definitions', return the list in sections.
    """
    # Break definitions:
    # Legacy: <verse_number>  or <chapter_number>:<verse_number>
    # New: canonical reference in the language.
    #   TODO - This means passage breaks won't work for versions in other languages,
    #     we need to fix this to be language agnostic

    # TODO - currently this has been modified to accept language_code, purely so
    # that we can pass it to parse_break_list. However, different grouping of
    # verses in different versions may mean we actually need to pass a
    # TextVersion through this, and other modified functions like
    # add_passage_breaks

    # Since the input has been sanitised, we can do parsing without needing DB
    # queries.
    if len(verse_list) == 0:
        return []

    if breaks == '':
        return [verse_list]

    break_ref_list = [p.get_start() for p in parse_break_list(language_code, breaks,
                                                              first_verse=verse_list[0])]

    sections = []
    current_section = []
    for v in verse_list:
        parsed_ref = parse_validated_localized_reference(
            language_code, v.localized_reference)
        start_ref = parsed_ref.get_start()
        if start_ref in break_ref_list and len(current_section) > 0:
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

    It returns a list of VerseSearchResult objects.
    """
    # Unlike fetch_localized_reference, this is tolerant with input.
    # It can still throw InvalidVerseReference for things that are obviously
    # incorrect e.g. Psalm 151, or asking for too many verses.

    ref_query = normalize_reference_input(version.language_code, query)
    search_query = query  # Leave alone, postgres to_tsquery does it right.

    if ref_query == '':
        raise InvalidVerseReference("Please enter a query term or reference")

    parsed_ref = parse_unvalidated_localized_reference(
        version.language_code,
        ref_query,
        allow_whole_book=not allow_searches)
    if parsed_ref is not None:
        verse_list = fetch_parsed_reference(version, parsed_ref,
                                            max_length=max_length)
        result_ref = normalized_verse_list_ref(version.language_code, verse_list)
        # parsed_ref might be difference from final_ref, due to merged verses
        parsed_result_ref = parse_validated_localized_reference(version.language_code,
                                                                result_ref)
        return [VerseSearchResult(result_ref, verse_list,
                                  parsed_ref=parsed_result_ref,
                                  from_reference=query)]

    if not allow_searches:
        raise InvalidVerseReference("Verse reference not recognized")

    # Do a search:
    searcher = get_search_service(version.slug)
    if searcher:
        return searcher(version, search_query)

    results = Verse.objects.text_search(search_query, version, limit=11)
    return [VerseSearchResult(r.localized_reference, [r]) for r in results]


def get_whole_book(book_name, version, ensure_text_present=True):
    retval = ComboVerse(book_name,
                        list(version.verse_set.filter(
                            book_number=get_bible_book_number(version.language_code, book_name),
                            missing=False)))
    if ensure_text_present:
        ensure_text(retval.verses)
    return retval
