from decimal import Decimal

from autoslug import AutoSlugField
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from learnscripture.datastructures import make_choices


BIBLE_BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']
BIBLE_BOOKS_DICT = dict((n, i) for (i, n) in enumerate(BIBLE_BOOKS))

# Psalm 119 is 176 verses
MAX_VERSE_QUERY_SIZE = 200
MAX_VERSES_FOR_SINGLE_CHOICE = 4


VerseSetType = make_choices('VerseSetType',
                            [(1, 'SELECTION', 'Selection'),
                             (2, 'PASSAGE', 'Passage'),
                            ])

StageType = make_choices('StageType',
                         [(1, 'READ', 'read'),
                          (2, 'RECALL_INITIAL', 'recall from initials'),
                          (3, 'RECALL_MISSING', 'recall when missing'),
                          (4, 'TEST_TYPE_FULL', 'test, typing full word'),
                          (5, 'TEST_TYPE_QUICK', 'test, typing initial'),
                          ])


# Various queries make use of the ordering in this enum, e.g. select everything
# less than 'TESTED'
MemoryStage = make_choices('MemoryStage',
                           [(1, 'ZERO', 'nothing'),
                            (2, 'SEEN', 'seen'),
                            (3, 'TESTED', 'tested'),
                            (4, 'LONGTERM', 'long term memory'),
                            ])


class BibleVersion(models.Model):
    short_name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255, unique=True)
    url = models.URLField(default="", blank=True)

    def __unicode__(self):
        return self.short_name


class Verse(models.Model):
    version = models.ForeignKey(BibleVersion)
    reference = models.CharField(max_length=100)
    text = models.TextField()

    # De-normalised fields
    # Public facing fields are 1-indexed, others are 0-indexed.
    book_number = models.PositiveSmallIntegerField() # 0-indexed
    chapter_number = models.PositiveSmallIntegerField() # 1-indexed
    verse_number = models.PositiveSmallIntegerField()   # 1-indexed
    bible_verse_number = models.PositiveSmallIntegerField() # 0-indexed

    @property
    def book_name(self):
        return BIBLE_BOOKS[self.book_number]

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


class VerseSet(models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(populate_from='name', null=True, unique=True)
    description = models.TextField(blank=True)
    set_type = models.PositiveSmallIntegerField(choices=VerseSetType.choice_list)

    popularity = models.PositiveIntegerField(default=0)
    date_added = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey('accounts.Account', related_name='verse_sets_created',
                                   null=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('view_verse_set', kwargs=dict(slug=self.slug))

class VerseChoiceManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return super(VerseChoiceManager, self).get_query_set().order_by('set_order')



# Note that VerseChoice and Verse are not related, since we want a VerseChoice
# to be independent of Bible version.
class VerseChoice(models.Model):
    reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, null=True, blank=True,
                                  related_name='verse_choices')
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
    Tracks the user's progress for a verse.
    """
    # It actually tracks the progress for a VerseChoice and Version.  This
    # implicitly allows it to track progress separately for different versions
    # and for the same verse in different verse sets.  In some cases this is
    # useful (for learning a passage, you might be learning a different version
    # to normal), but usually it is confusing, so business logic limits how much
    # this can happen

    for_identity = models.ForeignKey('accounts.Identity', related_name='verse_statuses')
    verse_choice = models.ForeignKey(VerseChoice)
    version = models.ForeignKey(BibleVersion)
    memory_stage = models.PositiveSmallIntegerField(choices=MemoryStage.choice_list,
                                                    default=MemoryStage.ZERO)
    strength = models.FloatField(default=0.00)
    added = models.DateTimeField(null=True, blank=True)
    first_seen = models.DateTimeField(null=True, blank=True)
    last_tested = models.DateTimeField(null=True, blank=True)

    # See Identity.change_version for explanation of ignored
    ignored = models.BooleanField(default=False)


    @cached_property
    def reference(self):
        return self.verse_choice.reference

    @cached_property
    def text(self):
        return ' '.join(v.text for v in parse_ref(self.reference, self.version))

    def __unicode__(self):
        return u"%s, %s" % (self.verse_choice.reference, self.version.slug)

    def __repr__(self):
        return u'<UserVerseStatus %s>' % self

    class Meta:
        unique_together = [('for_identity', 'verse_choice', 'version')]


class InvalidVerseReference(ValueError):
    pass

def parse_ref(reference, version, max_length=MAX_VERSE_QUERY_SIZE):
    """
    Takes a reference and returns the verses referred to in a list.
    """
    # This function is strict, and expects reference in normalised format.
    # Frontend function should deal with tolerance, to ensure that VerseChoice
    # only ever stores a canonical form.

    # This function will InvalidVerseReference if a verse is not matched.

    if ':' not in reference:
        # chapter only
        try:
            book, chapter = reference.rsplit(u' ')
        except ValueError:
            raise InvalidVerseReference(u"Reference should provide at least book name and chapter number")
        if book not in BIBLE_BOOKS_DICT:
            raise InvalidVerseReference(u"Book '%s' not known" % book)
        book_number = BIBLE_BOOKS_DICT.get(book)
        try:
            chapter_number = int(chapter)
        except ValueError:
            raise InvalidVerseReference(u"Expecting '%s' to be a chapter number" % chapter)
        retval = list(version.verse_set.filter(book_number=book_number, chapter_number=chapter_number))
    else:
        parts = reference.rsplit(u'-', 1)
        if len(parts) == 1:
            retval = list(version.verse_set.filter(reference=reference))

        else:
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

            # Try to get results in just two queries
            vs = version.verse_set.filter(reference__in=[ref_start, ref_end])
            try:
                verse_start, verse_end = tuple(vs)
            except ValueError:
                raise InvalidVerseReference(u"Can't find one '%s' or '%s'" % (ref_start, ref_end))

            if verse_end.bible_verse_number - verse_start.bible_verse_number > max_length:
                raise InvalidVerseReference(u"References that span more than %d verses are not allowed in this context." % max_length)

            retval = list(version.verse_set.filter(bible_verse_number__gte=verse_start.bible_verse_number,
                                                   bible_verse_number__lte=verse_end.bible_verse_number))
    if len(retval) == 0:
        raise InvalidVerseReference(u"No verses matched.")

    if len(retval) > max_length:
        raise InvalidVerseReference(u"References that span more than %d verses are not allowed in this context." % max_length)

    return retval


# Storing this is probably only useful for doing stats on progress and
# attempting to tune things.
class StageComplete(models.Model):
    verse_status = models.ForeignKey(UserVerseStatus)
    stage_type = models.PositiveSmallIntegerField(choices=StageType.choice_list)
    level = models.DecimalField(decimal_places=2, max_digits=3) # scale 0 to 1
    accuracy = models.DecimalField(decimal_places=2, max_digits=3) # scale 0 to 1
    date_completed = models.DateTimeField()
