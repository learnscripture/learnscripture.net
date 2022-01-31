import logging
import math
import operator
import random
from collections import defaultdict
from functools import reduce

import attr
from autoslug import AutoSlugField
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, Func, Q, Value
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from accounts import memorymodel
from learnscripture.datastructures import lazy_dict_like
from learnscripture.ftl_bundles import t, t_lazy
from learnscripture.utils.iterators import intersperse

from .books import get_bible_book_name, get_bible_book_number
from .fields import VectorField
from .languages import DEFAULT_LANGUAGE, LANGUAGE_CHOICES, LANGUAGE_CODE_EN, LANGUAGE_CODE_TR, normalize_reference_input
from .parsing import (
    InvalidVerseReference,
    ParsedReference,
    internalize_localized_reference,
    localize_internal_reference,
    parse_break_list,
    parse_passage_title_partial_loose,
    parse_unvalidated_localized_reference,
    parse_validated_internal_reference,
    parse_validated_localized_reference,
)
from .services import get_fetch_service, get_search_service
from .textutils import split_into_words

logger = logging.getLogger(__name__)


# Psalm 119 is 176 verses
MAX_VERSE_QUERY_SIZE = 200
MAX_VERSES_FOR_SINGLE_CHOICE = 4  # See also choose.js


# Also defined in Learn.elm verseSetTypeDecoder
class VerseSetType(models.TextChoices):
    SELECTION = "SELECTION", "Selection"
    PASSAGE = "PASSAGE", "Passage"


# Also defined in Learn.elm stageType* functions
class StageType(models.TextChoices):
    READ = "READ", "read"
    TEST = "TEST", "test"


# Various queries make use of the ordering in this enum, e.g. select everything
# less than 'TESTED'. Therefore it is import to be based on an integer.
class MemoryStage(models.IntegerChoices):
    ZERO = 1, "nothing"
    SEEN = 2, "seen"
    TESTED = 3, "tested"


# Also defined in Learn.elm textTypeDecoder
class TextType(models.TextChoices):
    BIBLE = "BIBLE", t_lazy("bibleverses-text-type-bible")
    CATECHISM = "CATECHISM", t_lazy("bibleverses-text-type-catechism")


class TextVersionQuerySet(models.QuerySet):
    def get_by_natural_key(self, slug):
        return self.get(slug=slug)

    def bibles(self):
        return self.filter(text_type=TextType.BIBLE)

    def catechisms(self):
        return self.filter(text_type=TextType.CATECHISM)

    def public(self):
        return self.filter(public=True)

    def visible_for_identity(self, identity):
        if identity is not None and identity.account_id is not None and identity.account.is_tester:
            return self
        return self.public()


class TextVersion(models.Model):
    short_name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255, unique=True)
    url = models.URLField(default="", blank=True)
    text_type = models.CharField(max_length=20, choices=TextType.choices, default=TextType.BIBLE)
    language_code = models.CharField(max_length=2, blank=False, choices=LANGUAGE_CHOICES, default=DEFAULT_LANGUAGE.code)
    description = models.TextField(blank=True)

    public = models.BooleanField(default=True)

    objects = TextVersionQuerySet.as_manager()

    @property
    def is_bible(self):
        return self.text_type == TextType.BIBLE

    @property
    def is_catechism(self):
        return self.text_type == TextType.CATECHISM

    class Meta:
        ordering = ["short_name"]

    def __str__(self):
        return f"{self.short_name} ({self.full_name})"

    def natural_key(self):
        return (self.slug,)

    def get_verse_list(self, localized_reference, max_length=MAX_VERSE_QUERY_SIZE):
        """
        Get ordered list of Verse objects for the given localized reference.
        (just one object for most references).
        """
        return fetch_localized_reference(self, self.language_code, localized_reference, max_length=max_length)

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
        return {r: v.text for (r, v) in verse_dict.items()}

    def get_verses_by_localized_reference_bulk(self, localized_reference_list, fetch_text=True):
        """
        Returns a dictionary of {localized_ref:verse} for each ref in localized_reference_list. Bad
        references are silently discarded, and won't be in the return
        dictionary.
        """
        if not self.is_bible:
            return {}
        return fetch_localized_reference_bulk(self, self.language_code, localized_reference_list, fetch_text=fetch_text)

    def get_verse_list_by_localized_reference_bulk(self, localized_reference_list, fetch_text=True):
        # Similar to get_verses_by_localized_reference_bulk, but returns a list, in the
        # same order as original list.
        verse_dict = self.get_verses_by_localized_reference_bulk(localized_reference_list, fetch_text=fetch_text)
        verse_list = []
        seen_actual_refs = set()
        # We cope with the fact that some things in localized_reference_list might be missing,
        # renamed or duplicated due to merged verses etc.
        for ref in localized_reference_list:
            if ref not in verse_dict:
                continue
            verse = verse_dict[ref]
            if verse.localized_reference in seen_actual_refs:
                continue
            seen_actual_refs.add(verse.localized_reference)
            verse_list.append(verse)
        return verse_list

    def get_qapairs_by_localized_reference_bulk(self, localized_reference_list):
        if not self.is_catechism:
            return {}
        return {
            qapair.localized_reference: qapair
            for qapair in self.qapairs.filter(localized_reference__in=localized_reference_list)
        }

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
        return [
            uvs.for_identity.account
            for uvs in UserVerseStatus.objects.select_related("for_identity", "for_identity__account").filter(
                version=self,
                text_order=1,
                for_identity__account__isnull=False,
                for_identity__account__is_active=True,
                for_identity__account__is_hellbanned=False,
            )
        ]

    # Simulate FK to WordSuggestionData
    @property
    def word_suggestion_data(self):
        from .suggestions.modelapi import word_suggestion_data_qs_for_version

        return word_suggestion_data_qs_for_version(self)

    @property
    def db_based_searching(self):
        return get_search_service(self.slug) is None

    def update_text_search(self, verses_qs):
        verses_qs.update(
            text_tsv=Func(
                Value(POSTGRES_SEARCH_CONFIGURATIONS[self.language_code]), F("text_saved"), function="to_tsvector"
            )
        )


class ComboVerse:
    """
    Wrapper needed when we want a combination of verses to appear as a single
    verse.
    """

    # Mimic Verse propeties

    def __init__(self, localized_reference, verse_list):
        self.localized_reference = localized_reference
        self.book_name = verse_list[0].book_name
        self.chapter_number = verse_list[0].chapter_number
        self.first_verse_number = verse_list[0].first_verse_number
        self.last_verse_number = verse_list[-1].last_verse_number
        self.bible_verse_number = verse_list[0].bible_verse_number
        self.gapless_bible_verse_number = verse_list[0].gapless_bible_verse_number
        self.verses = verse_list

    @property
    def text(self):
        # Do this lazily, so that we can update .text_saved in underlying Verse
        # objects if necessary.
        return " ".join(v.text for v in self.verses)

    @property
    def version(self):
        return self.verses[0].version

    @cached_property
    def internal_reference(self):
        return internalize_localized_reference(self.version.language_code, self.localized_reference)


class VerseSearchResult(ComboVerse):
    def __init__(self, localized_reference, verse_list, parsed_ref=None):
        super().__init__(localized_reference, verse_list)
        self.parsed_ref = parsed_ref


SEARCH_OPERATORS = {"&", "|", "@@", "@@@", "||", "&&", "!!", "@>", "<@", ":", "\\", "("}
SEARCH_CHARS = set("".join(list(SEARCH_OPERATORS)))


# See '\dF' command in psql for list of available builtin configurations.
POSTGRES_SEARCH_CONFIGURATIONS = {
    LANGUAGE_CODE_EN: "english",
    LANGUAGE_CODE_TR: "turkish",
}


class VerseManager(models.Manager):
    def get_by_natural_key(self, version_slug, localized_reference):
        return self.get(version__slug=version_slug, localized_reference=localized_reference)

    def text_search(self, query, version, limit=10, offset=0):
        # First remove anything recognized by postgres as an operator.
        for s in SEARCH_CHARS:
            query = query.replace(s, " ")
        words = query.split(" ")
        words = [w for w in words if (w and w not in SEARCH_OPERATORS)]
        # Do an 'AND' on all terms.
        word_params = list(intersperse(words, " & "))
        search_clause = " || ".join(["%s"] * len(word_params))
        search_config = POSTGRES_SEARCH_CONFIGURATIONS[version.language_code]
        return models.Manager.raw(
            self,
            """
          SELECT id, version_id, localized_reference, text_saved,
                 ts_headline(text_saved, query, 'StartSel = **, StopSel = **, HighlightAll=TRUE') as highlighted_text,
                 book_number, chapter_number, first_verse_number, last_verse_number,
                 bible_verse_number, gapless_bible_verse_number, ts_rank(text_tsv, query) as rank
          FROM bibleverses_verse, to_tsquery(%s, """
            + search_clause
            + """) query
          WHERE
             query @@ text_tsv
             AND version_id = %s
          ORDER BY rank DESC
          LIMIT %s
          OFFSET %s;
""",
            [search_config] + word_params + [version.id, limit, offset],
        )


class Verse(models.Model):
    """
    Stores a Bible verse contents and metadata
    """

    version = models.ForeignKey(TextVersion, on_delete=models.CASCADE)
    # Reference in the language of the text version e.g. "John 3:16" or "Yuhanna 3:16"
    localized_reference = models.CharField(max_length=100)
    # 'text_saved' is for data stored, as opposed to 'text' which might retrieve
    # from a service. Also, 'text_saved' is sometimes set without saving to the
    # DB, just so that 'text' can find it.
    text_saved = models.TextField(blank=True)
    # For text searching:
    text_tsv = VectorField()
    # For versions where we have fetched the text from a service
    text_fetched_at = models.DateTimeField(null=True, blank=True)

    # De-normalized fields - these can be derived from localized_reference
    # Public facing fields are 1-indexed, others are 0-indexed.
    book_number = models.PositiveSmallIntegerField()  # 0-indexed
    chapter_number = models.PositiveSmallIntegerField()  # 1-indexed
    first_verse_number = models.PositiveSmallIntegerField()  # 1-indexed
    # Usually last_verse_number is equal to first_verse_number,
    # it's only different for merged verses.
    last_verse_number = models.PositiveSmallIntegerField()  # 1-indexed

    # Position within the Bible:
    bible_verse_number = models.PositiveSmallIntegerField()  # 0-indexed

    # gapless_bible_verse_number differs from bible_verse_number in that when
    # missing and merged verses are removed, it has no gaps,
    # while bible_verse_number does. In other words, if you step through
    # gapless_bible_verse_number, incrementing by one, you will always
    # get to another verse with content, until the very last verse.
    # 0 indexed.
    gapless_bible_verse_number = models.PositiveIntegerField(null=True)

    # This field is to cope with versions where a specific verse is entirely
    # empty e.g. John 5:4 in NET/ESV
    missing = models.BooleanField(default=False)

    # For versions that do merged verses, we have dummy Verse objects for the
    # unmerged references. e.g. in TCL02, there is 'Yuhanna 1:19-20'. For
    # 'Yuhanna 1:19' and 'Yuhanna 1:20', we have Verse objects that have
    # text_saved == '' (and gapless_bible_verse_number == NULL), but
    # 'merged_into' points to 'Yuhanna 1:19-20' (which has content in text_saved
    # and a non-NULL gapless_bible_verse_number).
    merged_into = models.ForeignKey("self", on_delete=models.CASCADE, related_name="merged_from", blank=True, null=True)

    objects = VerseManager()

    @property
    def text(self):
        if self.text_saved == "" and not self.missing:
            # We should not reach this, verses with empty `text_saved` should be
            # populated from a service **in bulk** for efficiency using things
            # like get_verses_by_localized_reference_bulk. But in case we do we
            # warn rather than error.
            logger.warning(
                "Reached ensure_text call from Verse.text, for %s %s", self.version.slug, self.localized_reference
            )
            ensure_text([self])
        return self.text_saved

    @cached_property
    def display_verse_number(self):
        if self.last_verse_number == self.first_verse_number:
            return str(self.first_verse_number)
        else:
            return f"{self.first_verse_number}-{self.last_verse_number}"

    @property
    def book_name(self):
        return get_bible_book_name(self.version.language_code, self.book_number)

    def natural_key(self):
        return (self.version.slug, self.localized_reference)

    def __str__(self):
        return f"{self.localized_reference} ({self.version.short_name})"

    def __repr__(self):
        return f"<Verse {self}>"

    class Meta:
        unique_together = [
            ("version", "bible_verse_number"),
            ("version", "gapless_bible_verse_number"),
            ("version", "localized_reference"),
        ]
        ordering = ("bible_verse_number",)

    def mark_missing(self):
        self.missing = True
        self.save()
        UserVerseStatus.objects.filter(version=self.version, localized_reference=self.localized_reference).delete()

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

    @cached_property
    def internal_reference(self):
        return internalize_localized_reference(self.version.language_code, self.localized_reference)


SUGGESTION_COUNT = 10


class WordSuggestionData(models.Model):
    # All the suggestion data for a single verse/question
    # For efficiency, we avoid having millions of rows, because
    # we always need all the suggestions for a verse together.

    # For practical reasons, this table is stored in a separate DB, so it has no
    # explicit FKs to the main DB.
    version_slug = models.CharField(max_length=20, default="")
    localized_reference = models.CharField(max_length=100)
    hash = models.CharField(max_length=40)  # SHA1 of text

    # Schema: list of suggestions for each word, in order. each suggestion
    # consists of a list of words in decreasing order of fitness.
    # So we have
    # [[suggestion_1_for_word_1, s_2_for_w_1,...],[s_1_for_w_2, s_2_for_w_2]]
    suggestions = models.JSONField(default=list)

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
            pairs = [(word, 1.0 - i * 0.5 / len(word_suggestions)) for i, word in enumerate(word_suggestions)]

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
        unique_together = [("version_slug", "localized_reference")]

    def __repr__(self):
        return f"<WordSuggestionData {self.version_slug} {self.localized_reference}>"


class QAPairManager(models.Manager):
    def get_by_natural_key(self, catechism_slug, localized_reference):
        return self.get(catechism__slug=catechism_slug, localized_reference=localized_reference)


class QAPair(models.Model):
    """
    A question/answer pair in a catechism.
    """

    catechism = models.ForeignKey(TextVersion, on_delete=models.CASCADE, related_name="qapairs")
    # localized_reference is always 'Qn' where 'n' == order. (Apart from where
    # we have question numbers like '2a').
    # localized_reference is referred to by UserVerseStatus
    localized_reference = models.CharField(max_length=100)
    question = models.TextField()
    answer = models.TextField()
    order = models.PositiveSmallIntegerField()

    objects = QAPairManager()

    class Meta:
        unique_together = [("catechism", "order"), ("catechism", "localized_reference")]

        verbose_name = "QA pair"
        ordering = ["order"]

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


class VerseSetQuerySet(models.QuerySet):
    def visible_for_account(self, account):
        qs = self.public()
        if account is None or not account.is_hellbanned:
            qs = qs.exclude(created_by__is_hellbanned=True)

        if account is not None:
            qs = qs | account.verse_sets_created.all()

        return qs

    def public(self):
        return self.filter(public=True)

    def search(self, language_codes, query, default_language_code=None):
        if not query:
            return self.filter(language_code__in=language_codes) | self.filter(any_language=True)

        result_queries = []
        # If we are searching multiple languages, but using a verse ref, we will
        # need to parse the verse ref in the language that matches e.g.
        # "Yarat 1:1" should parse to 'BOOK0 1:1', and we then search all
        # VerseSets in all languages that match.
        parsed_refs = {}
        for language_code in language_codes:
            # Does the query look like a Bible reference?
            try:
                parsed_ref = parse_unvalidated_localized_reference(
                    language_code, query, allow_whole_book=False, allow_whole_chapter=True
                )
            except InvalidVerseReference:
                # For invalid verse references, it looks like a verse ref,
                # but refers to something that doesn't exist e.g. "Gen 73:1".
                # It should get no results.
                continue
            if parsed_ref is not None:
                parsed_refs[language_code] = parsed_ref

        if len(parsed_refs) == 0:
            fallback_parsed_ref = None
        else:
            try:
                fallback_parsed_ref = parsed_refs[default_language_code]
            except KeyError:
                # We have potentially multiple parsed references, none of them
                # in the default language, and potentially all of them referring
                # to different verses. Can't do much here so just pick one.
                fallback_parsed_ref = list(parsed_refs.values())[0]

        for language_code in language_codes:
            initial_verse_sets = self.filter(language_code=language_code) | self.filter(any_language=True)
            parsed_ref = parsed_refs.get(language_code, fallback_parsed_ref)
            if parsed_ref is not None:
                if parsed_ref.start_verse is None:
                    # To find a whole chapter, look for sets containing first verse.
                    search_parsed_ref = attr.evolve(parsed_ref, start_verse=1)
                    # But limit to only passage types, otherwise we'll get false
                    # positives for selection sets that contain other verses
                    # from that chapter.
                    result_queries.append(
                        initial_verse_sets.filter(
                            set_type=VerseSetType.PASSAGE,
                            verse_choices__internal_reference=search_parsed_ref.to_internal().canonical_form(),
                        )
                    )
                else:
                    if parsed_ref.get_start() != parsed_ref.get_end():
                        # Looks like passage ref:
                        result_queries.append(
                            initial_verse_sets.filter(
                                set_type=VerseSetType.PASSAGE,
                                passage_id=make_verse_set_passage_id(
                                    parsed_ref.get_start().to_internal(), parsed_ref.get_end().to_internal()
                                ),
                            )
                        )
                    else:
                        result_queries.append(
                            initial_verse_sets.filter(
                                set_type__in=[VerseSetType.SELECTION, VerseSetType.PASSAGE],
                                verse_choices__internal_reference=parsed_ref.to_internal().canonical_form(),
                            )
                        )
            else:
                result_queries.append(initial_verse_sets.filter(name__icontains=query))
        if result_queries:
            return reduce(operator.or_, result_queries)
        else:
            return self.none()


class VerseSetManager(models.Manager.from_queryset(VerseSetQuerySet)):
    def popularity_for_sets(self, ids, ignoring_account_ids):
        """
        Gets the 'popularity' for a group of sets, using actual usage.
        """
        if len(ids) == 0:
            return 0
        return (
            UserVerseStatus.objects.active()
            .exclude(for_identity__account__isnull=True)
            .exclude(for_identity__account__in=ignoring_account_ids)
            .filter(verse_set__in=ids)
            .aggregate(count=models.Count("for_identity", distinct=True))["count"]
        )


class VerseSet(models.Model):
    name = models.CharField(t_lazy("versesets-name"), max_length=255)
    slug = AutoSlugField(populate_from="name", unique=True)
    description = models.TextField(t_lazy("versesets-description"), blank=True)
    additional_info = models.TextField(t_lazy("versesets-additional-info"), blank=True)
    set_type = models.CharField(max_length=20, choices=VerseSetType.choices)

    public = models.BooleanField(t_lazy("versesets-public"), default=False)
    breaks = models.TextField(default="", blank=True)

    popularity = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="verse_sets_created")

    # Essentially denormalized field, to make it quick to check for duplicate
    # passage sets:
    passage_id = models.CharField(max_length=203, blank=True, default="")  # 100 for reference * 2 + 3 for ' - '

    language_code = models.CharField(
        t_lazy("versesets-language"),
        max_length=2,
        blank=False,
        help_text=t_lazy("versesets-language.help-text"),
        choices=LANGUAGE_CHOICES,
    )
    # A verse set is 'any_language' if it title/description can be automatically
    # translated (i.e. contains only bible references)
    any_language = models.BooleanField(default=False)

    objects = VerseSetManager()

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        self._update_passage_id()
        self._update_any_language()
        super().save(**kwargs)

    def get_absolute_url(self):
        return reverse("view_verse_set", kwargs=dict(slug=self.slug))

    @property
    def is_passage(self):
        return self.set_type == VerseSetType.PASSAGE

    @property
    def is_selection(self):
        return self.set_type == VerseSetType.SELECTION

    @property
    def breaks_formatted(self):
        return ", ".join(f"{pr.start_chapter}:{pr.start_verse}" for pr in parse_break_list(self.breaks))

    def set_verse_choices(self, internal_reference_list):
        existing_vcs = self.verse_choices.all()
        existing_vcs_dict = {vc.internal_reference: vc for vc in existing_vcs}
        old_vcs = set(existing_vcs)
        seen = set()
        for i, ref in enumerate(internal_reference_list):  # preserve order
            if ref in seen:
                # dedupe
                continue
            seen.add(ref)
            # Sanitise:
            try:
                parsed_ref = parse_validated_internal_reference(ref)
            except InvalidVerseReference:
                continue
            if not parsed_ref.is_in_bounds():
                continue
            dirty = False
            if ref in existing_vcs_dict:
                vc = existing_vcs_dict[ref]
                if vc.set_order != i:
                    vc.set_order = i
                    dirty = True
                old_vcs.remove(vc)
            else:
                vc = VerseChoice(verse_set=self, internal_reference=ref, set_order=i)
                dirty = True
            if dirty:
                vc.save()

        # Delete unused VerseChoice objects.
        for vc in old_vcs:
            vc.delete()

        self.save()  # to run update_passage_id and save

    def _update_passage_id(self):
        if self.is_passage:
            verse_choices = list(self.verse_choices.all())
            if len(verse_choices) == 0:
                self.passage_id = ""
                return
            self.passage_id = make_verse_set_passage_id(
                verse_choices[0].internal_reference, verse_choices[-1].internal_reference
            )
        else:
            self.passage_id = ""

    def _update_any_language(self):
        # If a verse set is for a passage, and the name can be fully translated,
        # with no other text to translate, we can treat the verse set as 'any language'.
        any_language = False
        if self.is_passage and self.description.strip() == "":
            parsed_ref, complete_parse = parse_passage_title_partial_loose(self.language_code, self.name)
            if parsed_ref is not None and complete_parse:
                any_language = True
        self.any_language = any_language

    def smart_name(self, required_language_code):
        """
        Attempt to translate verse references in a VerseSet name into user's language
        """
        return verse_set_smart_name(self.name, self.language_code, required_language_code)

    # For use in templates:
    @lazy_dict_like
    def smart_name_dict(self, language_code):
        return self.smart_name(language_code)


def verse_set_smart_name(verse_set_name, verse_set_language_code, required_language_code):
    """
    Given a verse set name which might be a passage ref, try to intelligently translate
    from the given language to required language
    """
    if required_language_code == verse_set_language_code:
        return verse_set_name

    # Passage set names are often just the passage ref (this is set automatically),
    # or start with the passage ref.
    parsed_ref, complete_parse = parse_passage_title_partial_loose(verse_set_language_code, verse_set_name)

    if parsed_ref is None:
        return verse_set_name

    required_localized_ref = parsed_ref.translate_to(required_language_code).canonical_form()
    if complete_parse:
        # Just the passage ref
        return required_localized_ref
    else:
        return verse_set_name.strip() + " (" + required_localized_ref + ")"


def make_verse_set_passage_id(start_internal_reference, end_internal_reference):
    if isinstance(start_internal_reference, ParsedReference):
        parsed_start_ref = start_internal_reference
    else:
        parsed_start_ref = parse_validated_internal_reference(start_internal_reference)
    if isinstance(end_internal_reference, ParsedReference):
        parsed_end_ref = end_internal_reference
    else:
        parsed_end_ref = parse_validated_internal_reference(end_internal_reference)
    return ParsedReference.from_start_and_end(
        parsed_start_ref,
        parsed_end_ref,
    ).canonical_form()


def verse_set_passage_id_to_parsed_ref(passage_id):
    return parse_validated_internal_reference(passage_id)


class VerseChoiceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("set_order")


# Note that VerseChoice and Verse are not related, since we want a VerseChoice
# to be independent of Bible version.
class VerseChoice(models.Model):
    internal_reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, on_delete=models.PROTECT, related_name="verse_choices")
    set_order = models.PositiveSmallIntegerField(default=0)

    objects = VerseChoiceManager()

    class Meta:
        unique_together = [
            ("verse_set", "internal_reference"),
        ]
        base_manager_name = "objects"

    def __str__(self):
        return self.internal_reference

    def __repr__(self):
        return f"<VerseChoice {self}>"

    def get_localized_reference(self, language_code):
        return localize_internal_reference(language_code, self.internal_reference)

    # For use in templates:
    @lazy_dict_like
    def localized_reference_dict(self, language_code):
        return self.get_localized_reference(language_code)


class UserVerseStatusQuerySet(models.QuerySet):
    def active(self):
        # See also UserVerseStatus.is_active
        return self.filter(ignored=False)

    def tested(self):
        # See also UserVerseStatus.is_tested
        return self.active().filter(
            memory_stage=MemoryStage.TESTED,
        )

    def reviewable(self):
        # See also UserVerseStatus.is_reviewable
        return (
            self.active()
            .tested()
            .filter(
                Q(strength__lt=memorymodel.LEARNT) | Q(early_review_requested=True),
                next_test_due__isnull=False,
            )
        )

    def needs_reviewing(self, now):
        # See also UserVerseStatus.needs_reviewing
        return self.reviewable().filter(next_test_due__lte=now)

    def needs_reviewing_in_future(self, now):
        return self.reviewable().filter(next_test_due__gt=now)

    def search_by_parsed_ref(self, parsed_ref):
        if not parsed_ref.is_in_bounds():
            return self.none()
        if parsed_ref.is_whole_book():
            # To avoid large number of parameters involved in doing 'to_list()'
            # on a whole book, do this.
            # This is a bit hacky...
            return self.filter(internal_reference_list__0__startswith=parsed_ref.to_internal().canonical_form() + " ")
        refs = [ref.canonical_form() for ref in parsed_ref.to_internal().to_list()]
        return self.filter(internal_reference_list__overlap=refs)

    def total_tested_today_count(self):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            self.active()
            .filter(last_tested__gte=today_start)
            .values("version_id", "localized_reference")
            .distinct()
            .count()
        )

    def started_today_count(self):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            self.active()
            .filter(first_seen__gte=today_start)
            .values("version_id", "localized_reference")
            .distinct()
            .count()
        )


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

    for_identity = models.ForeignKey("accounts.Identity", on_delete=models.CASCADE, related_name="verse_statuses")
    localized_reference = models.CharField(max_length=100)
    internal_reference_list = ArrayField(models.CharField(max_length=100), default=list)
    verse_set = models.ForeignKey(VerseSet, null=True, blank=True, on_delete=models.SET_NULL)
    text_order = models.PositiveSmallIntegerField()  # order of this item within associated TextVersion
    version = models.ForeignKey(TextVersion, on_delete=models.PROTECT)

    # The following fields vary over time and care should be taken in things
    # like create_verse_status to copy these attributes if there are duplicates.
    memory_stage = models.PositiveSmallIntegerField(choices=MemoryStage.choices, default=MemoryStage.ZERO)
    strength = models.FloatField(default=0.00)
    added = models.DateTimeField()
    first_seen = models.DateTimeField(null=True, blank=True)
    last_tested = models.DateTimeField(null=True, blank=True)
    next_test_due = models.DateTimeField(null=True, blank=True)
    early_review_requested = models.BooleanField(default=False)

    # ignored is True when users have chosen to stop learning a verse.
    ignored = models.BooleanField(default=False)

    objects = models.Manager.from_queryset(UserVerseStatusQuerySet)()

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
        return self.localized_reference + ("" if self.version.is_bible else ". " + self.question)

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

    @property
    def needs_testing(self):
        if hasattr(self, "needs_testing_override"):
            return self.needs_testing_override
        else:
            return self.needs_testing_individual

    @cached_property
    def needs_testing_individual(self):
        # We go by 'next_test_due', since that is how we do filtering.
        if self.last_tested is None:
            return True
        if self.next_test_due is None:
            return True
        if self.strength >= memorymodel.LEARNT and not self.early_review_requested:
            return False
        return timezone.now() >= self.next_test_due

    def is_in_passage(self):
        return self.verse_set is not None and self.verse_set.is_passage

    def is_active(self):
        # Seel also UserVerseStatusQuerySet.active
        return not self.ignored

    def is_tested(self):
        # Seel also UserVerseStatusQuerySet.tested
        return self.is_active() and self.memory_stage == MemoryStage.TESTED

    def is_reviewable(self):
        # See also UserVerseStatusQuerySet.reviewable()
        return (
            self.is_active()
            and self.is_tested()
            and ((self.strength < memorymodel.LEARNT or self.early_review_requested) and self.next_test_due is not None)
        )

    def needs_reviewing(self, now):
        # See also UserVerseStatusQuerySet.needs_reviewing()
        return self.is_reviewable() and self.next_test_due <= now

    def scaled_strength(self):
        # See also Learn.elm scaledStrength. Anything more than LEARNT is
        # counted as fully learnt, so we re-scaled according to that, only for
        # the purposes of user presentation.
        return min(self.strength / memorymodel.LEARNT, 1.0)

    def scaled_strength_percentage(self):
        return math.floor(self.scaled_strength() * 100)

    @cached_property
    def passage_localized_reference(self):
        """
        Returns the localized reference for the whole passage this UVS belongs to.
        """
        if not self.is_in_passage():
            return None
        passage_status_list = self.get_verse_set_verse_status_list()
        return normalized_verse_list_ref(self.version.language_code, passage_status_list)

    @cached_property
    def verse_set_choices(self):
        return list(self.verse_set.verse_choices.all())

    @cached_property
    def section_localized_reference(self):
        """
        Returns the localized reference for the section in the passage this UVS belongs to.
        """
        if not self.is_in_passage():
            return None

        section_status_list = self.get_section_verse_status_list(self.get_verse_set_verse_status_list())
        return normalized_verse_list_ref(self.version.language_code, section_status_list)

    def get_verse_set_verse_status_list(self):
        return list(
            UserVerseStatus.objects.filter(
                verse_set=self.verse_set_id, for_identity=self.for_identity_id, version=self.version_id
            ).order_by("text_order")
        )

    def get_section_verse_status_list(self, passage_uvs_list):
        """
        Returns the UVS list for the passage section the current UVS is a part of,
        given an ordered UVS list for the whole passage.
        """
        sections = get_passage_sections(passage_uvs_list, self.verse_set.breaks)
        for section in sections:
            if self in section:
                return section

    # This will be overwritten by get_verse_statuses_bulk
    @cached_property
    def suggestions(self):
        return self.version.get_suggestions_by_localized_reference(self.localized_reference)

    def __str__(self):
        return f"{self.localized_reference}, {self.version.slug}"

    def __repr__(self):
        return f"<UserVerseStatus {self}>"

    class Meta:
        unique_together = [("for_identity", "verse_set", "localized_reference", "version")]
        verbose_name_plural = "User verse statuses"


#  ---- Verse fetching ----
#
# This is significantly complicated by several factors:
#
# * We sometimes want to fetch in bulk - for example, when starting a learning
#   session for a set of UserVerseStatuses - and sometimes just want a single
#   'thing'. This results in many functions having two versions, bulk and
#   non-bulk for efficiency.
#
# * We sometimes want to parse verse references loosely (e.g. from non-canonical
#   user entered data)
#
# * We need to handle:
#   - Combo verses (e.g. when a user chooses to learn several verses
#     together as single verse e.g. Ephesians 2:8-9)
#   - Passages - we want to retrieve all of "John 1:1-15", to be displayed in a list
#     (but we display each verse individually)
#   - Merged verses - where the underlying Bible translation has put several
#     verses together e.g. TCL02 Romalılar 3:25-26.
#   - Missing verses - where the translation doesn't have a certain verse.
#
# * We may need to tolerate some incorrectness in requested references e.g. not
#   accounting for merged verses in underlying translation, and do something
#   sensible.
#
# * For some TextVersions we don't store the whole text locally due to license
#   agreements. We only have a limited local cache and must get the remainder
#   from a service (but avoid doing so wherever possible).
#
# * And then the combination of all these (e.g. merged verses and combo verses)
#   with the edge cases, combined with trying to get data efficiently with the
#   minimum of DB queries.


class TooManyVerses(InvalidVerseReference):
    pass


def fetch_localized_reference(version, language_code, localized_reference, max_length=MAX_VERSE_QUERY_SIZE):
    parsed_ref = parse_validated_localized_reference(language_code, localized_reference)
    return fetch_parsed_reference(version, parsed_ref, max_length=max_length)


def fetch_parsed_reference(version, parsed_ref, max_length=MAX_VERSE_QUERY_SIZE):
    """
    Fetch the ParsedReference from the DB, return
    as a list of Verse objects.

    References that are incorrect due to merged verses will be automatically
    corrected.

    If otherwise incorrect, InvalidVerseReference will be raised
    """
    if parsed_ref.is_whole_chapter():
        retval = list(
            version.verse_set.filter(
                book_number=parsed_ref.book_number, chapter_number=parsed_ref.start_chapter, missing=False
            ).order_by("bible_verse_number")
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
        # So we just miss out the missing verses later when creating the list.
        vs = version.verse_set.filter(localized_reference__in=[ref_start, ref_end])
        try:
            verse_start = [v for v in vs if v.localized_reference == ref_start][0]
        except IndexError:
            raise InvalidVerseReference(f"Can't find  '{ref_start}'")
        try:
            verse_end = [v for v in vs if v.localized_reference == ref_end][0]
        except IndexError:
            raise InvalidVerseReference(f"Can't find  '{ref_end}'")

        if verse_end.bible_verse_number < verse_start.bible_verse_number:
            raise InvalidVerseReference(f"{ref_start} and {ref_end} are not in ascending order.")

        items = version.verse_set.filter(
            bible_verse_number__gte=verse_start.bible_verse_number, bible_verse_number__lte=verse_end.bible_verse_number
        ).select_related("merged_into")
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
        raise InvalidVerseReference(t("bibleverses-no-verses-matched-ref", dict(ref=parsed_ref.canonical_form())))

    if len(retval) > max_length:
        raise TooManyVerses(t("bibleverses-too-many-verses", dict(allowed=max_length)))

    # Ensure back references to version are set, so we don't need extra DB lookup
    for v in retval:
        v.version = version
    # Ensure verse.text_saved is set
    ensure_text(retval)

    return retval


def fetch_localized_reference_bulk(version, language_code, localized_reference_list, fetch_text=True):
    """
    Returns a dictionary {ref: Verse or ComboVerse} for refs matching the requested references.
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
                vl = fetch_localized_reference(version, language_code, localized_ref)
                # In theory, localized_reference_list should already have been
                # corrected for merged verses. But if it has not been, this will
                # correct it so that the ComboVerse has the correct reference.
                normalized_localized_ref = normalized_verse_list_ref(language_code, vl)
                v_dict[localized_ref] = ComboVerse(normalized_localized_ref, vl)
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
    verses = version.verse_set.filter(localized_reference__in=localized_reference_list).select_related("merged_into")
    verse_d = {v.localized_reference: v for v in verses}

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
            if hasattr(v, "verses"):
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
        if v.text_saved == "" and not v.missing:
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
        if v.text_saved == "" and not v.missing:
            logger.warning("Marking %s %s as missing", v.version.slug, v.localized_reference)
            v.missing = True
            v.save()


def normalized_verse_list_ref(language_code, verse_list):
    if len(verse_list) == 1:
        return verse_list[0].localized_reference
    else:
        return ParsedReference.from_start_and_end(
            parse_validated_localized_reference(language_code, verse_list[0].localized_reference),
            parse_validated_localized_reference(language_code, verse_list[-1].localized_reference),
        ).canonical_form()


def is_continuous_set(verse_list):
    if len(verse_list) in [0, 1]:
        # not enough to be considered continuous
        return False

    # We could use gapless_bible_verse_number here to detect continuous sets.
    # However, that would not cover the case where a set has been put together
    # using Combo verses, which is possible and might be desirable if some
    # verses in a passage are very short.
    verse_list = sorted(verse_list, key=lambda v: v.bible_verse_number)
    version = verse_list[0].version
    try:
        combined_ref = normalized_verse_list_ref(version.language_code, verse_list)
    except InvalidVerseReference:
        return False
    # Quick heuristic to stop us fetching lots of stuff:
    parsed_combined_ref = parse_validated_localized_reference(version.language_code, combined_ref)
    chapter_count = abs(parsed_combined_ref.end_chapter - parsed_combined_ref.start_chapter)
    if chapter_count > 1:
        # Most chapters have more than 20 verses
        if len(verse_list) / chapter_count < 20:
            return False

    try:
        combined = fetch_localized_reference(version, version.language_code, combined_ref)
    except TooManyVerses:
        return False  # Can't do anything else.

    return [v.localized_reference for v in verse_list] == [v.localized_reference for v in combined]


def get_passage_sections(verse_list, breaks):
    """
    Given a list of objects with either a correct 'localized_reference' or
    'internal_reference' attribute, and a break list (a comma separated list of
    internal references), return the list in sections.
    """
    # Since the input has been sanitised, we can do parsing without needing DB
    # queries.
    if len(verse_list) == 0:
        return []

    if breaks == "":
        return [verse_list]

    break_ref_list = [p.get_start() for p in parse_break_list(breaks)]

    sections = []
    current_section = []
    for v in verse_list:
        if hasattr(v, "internal_reference"):
            parsed_ref = parse_validated_internal_reference(v.internal_reference)
        else:
            parsed_ref = parse_validated_localized_reference(
                v.version.language_code, v.localized_reference
            ).to_internal()
        start_ref = parsed_ref.get_start()
        if start_ref in break_ref_list and len(current_section) > 0:
            # Start new section
            sections.append(current_section)
            current_section = []
        current_section.append(v)
    sections.append(current_section)
    return sections


QUICK_FIND_SEARCH_LIMIT = 10


def quick_find(
    query,
    version,
    max_length=MAX_VERSES_FOR_SINGLE_CHOICE,
    page=0,
    page_size=QUICK_FIND_SEARCH_LIMIT,
    allow_searches=True,
):
    """
    Does a verse search based on reference or contents.

    It returns (list of VerseSearchResult objects, more results available boolean)

    It will return at most page_size items
    """
    # Unlike fetch_localized_reference, this is tolerant with input.
    # It can still throw InvalidVerseReference for things that are obviously
    # incorrect e.g. Psalm 151, or asking for too many verses.

    ref_query = normalize_reference_input(version.language_code, query)
    search_query = query  # Leave alone, postgres to_tsquery does it right.

    if ref_query == "":
        raise InvalidVerseReference(t("bibleverses-no-query-term"))

    parsed_ref = parse_unvalidated_localized_reference(
        version.language_code, ref_query, allow_whole_book=not allow_searches
    )
    if parsed_ref is not None:
        verse_list = fetch_parsed_reference(version, parsed_ref, max_length=max_length)
        result_ref = normalized_verse_list_ref(version.language_code, verse_list)
        # parsed_ref might be difference from result_ref, due to merged verses
        parsed_result_ref = parse_validated_localized_reference(version.language_code, result_ref)
        return ([VerseSearchResult(result_ref, verse_list, parsed_ref=parsed_result_ref)], False)

    if not allow_searches:
        raise InvalidVerseReference(t("bibleverses-verse-reference-not-recognized"))

    # Do a search:
    searcher = get_search_service(version.slug)
    if searcher:
        return searcher(version, search_query, page, page_size)

    results = list(Verse.objects.text_search(search_query, version, limit=page_size + 1, offset=page * page_size))
    more_results = len(results) > page_size
    return [VerseSearchResult(r.localized_reference, [r]) for r in results[0:page_size]], more_results


def get_whole_book(book_name, version, ensure_text_present=True):
    retval = ComboVerse(
        book_name,
        list(
            version.verse_set.filter(book_number=get_bible_book_number(version.language_code, book_name), missing=False)
        ),
    )
    if ensure_text_present:
        ensure_text(retval.verses)
    return retval
