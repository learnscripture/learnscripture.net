from decimal import Decimal

from django.db import models

from learnscripture.datastructures import make_choices


VerseSetType = make_choices('VerseSetType',
                            [(1, 'TOPIC', 'Topic'),
                             (2, 'PASSAGE', 'Passage'),
                             (3, 'GENERAL', 'General'),
                            ])

StageType = make_choices('StageType',
                         [(1, 'READ', 'read'),
                          (2, 'RECALL_INITIAL', 'recall from initials'),
                          (3, 'RECALL_MISSING', 'recall when missing'),
                          (4, 'TEST_TYPE_INITIAL', 'test, typing initial'),
                          (5, 'TEST_TYPE_COMPLETE', 'test, typing completing word from initial'),
                          (6, 'TEST_TYPE_FULL', 'test, typing full word'),
                          ])


MemoryStage = make_choices('MemoryStage',
                           [(1, 'ZERO', 'nothing'),
                            (2, 'SHORTTERM', 'short term memory'),
                            (3, 'LONGTERM', 'long term memory'),
                            ])


class BibleVersion(models.Model):
    short_name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.short_name


class Verse(models.Model):
    version = models.ForeignKey(BibleVersion)
    reference = models.CharField(max_length=100)
    text = models.TextField()

    def __unicode__(self):
        return "%s (%s)" % (self.reference, self.version.short_name)


class VerseSet(models.Model):
    name = models.CharField(max_length=255, unique=True)
    set_type = models.PositiveSmallIntegerField(choices=VerseSetType.choice_list)

    def __unicode__(self):
        return self.name



# Note that VerseChoice and Verse are not related, since we want a VerseChoice
# to be independent of Bible version.
class VerseChoice(models.Model):
    reference = models.CharField(max_length=100)
    verse_set = models.ForeignKey(VerseSet, null=True, blank=True,
                                  related_name='verses')
    set_order = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [('verse_set', 'reference')]

    def __unicode__(self):
        return self.reference


class UserVerseStatus(models.Model):
    for_identity = models.ForeignKey('accounts.Identity', related_name='verse_statuses')
    verse = models.ForeignKey(VerseChoice)
    version = models.ForeignKey(BibleVersion)
    memory_stage = models.PositiveSmallIntegerField(choices=MemoryStage.choice_list,
                                                    default=MemoryStage.ZERO)
    strength = models.DecimalField(default=Decimal('0.00'), decimal_places=2, max_digits=3)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()


# Storing this is probably only useful for doing stats on progress and
# attempting to tune things.
class StageComplete(models.Model):
    verse_status = models.ForeignKey(UserVerseStatus)
    stage_type = models.PositiveSmallIntegerField(choices=StageType.choice_list)
    level = models.DecimalField(decimal_places=2, max_digits=3) # scale 0 to 1
    accuracy = models.DecimalField(decimal_places=2, max_digits=3) # scale 0 to 1
    date_completed = models.DateTimeField()
