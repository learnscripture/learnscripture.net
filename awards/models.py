from django.db import models
from django.utils import timezone

from accounts.models import Account
from awards.signals import new_award
from learnscripture.datastructures import make_choices

AwardType = make_choices('AwardType',
                         [(0, 'STUDENT', 'Student'),
                          (1, 'MASTER', 'Master'),
                          (2, 'SHARER', 'Sharer'),
                          ])

class CountBasedAward(object):

    # Subclass must define COUNTS

    def __init__(self, level=None, count=None):
        """
        Must pass at least one of level or count
        """
        self._LEVELS_DESC = sorted([(a,b) for b, a in self.COUNTS.items()], reverse=True)
        if count is None:
            self.count = self.count_for_level(level)
        else:
            self.count = count

        if level is None:
            self.level = self.level_for_count(count)
        else:
            self.level = level

    def level_for_count(self, count):
        for c, level in self._LEVELS_DESC:
            if count >= c:
                return level
        return 0

    def count_for_level(self, level):
        return self.COUNTS[level]


class LearningAward(CountBasedAward):
    COUNTS = {1: 1,
              2: 10,
              3: 30,
              4: 100,
              5: 300,
              6: 1000,
              7: 3000,
              8: 10000,
              9: 31102, # every verse
              }


class StudentAward(LearningAward):
    def full_description(self):
        if self.level == 1:
            return u"Learning at least one verse"
        elif self.level == 9:
            return u"Learning the whole bible!"
        else:
            return u"Learning at least %s verses" % self.count


class MasterAward(LearningAward):
    def full_description(self):
        if self.level == 1:
            return u"Finished learning at least one verse"
        elif self.level == 9:
            return u"Finished learning the whole bible!"
        else:
            return u"Finished learning at least %s verses" % self.count


class SharerAward(CountBasedAward):
    COUNTS = {1: 1,
              2: 2,
              3: 5,
              4: 10,
              5: 20,
              }

    def full_description(self):
        if self.level == 1:
            return u"Created a public selection verse set"
        else:
            return u"Created %d public selection verse sets" % self.count


AWARD_CLASSES = {
    AwardType.STUDENT: StudentAward,
    AwardType.MASTER: MasterAward,
    AwardType.SHARER: SharerAward,
}

for t, c in AWARD_CLASSES.items():
    c.award_type = t


class AwardManager(models.Manager):

    def get_or_create(self, *args, **kwargs):
        award, new = super(AwardManager, self).get_or_create(*args, **kwargs)
        if new:
            new_award.send(sender=award)
        return (award, new)


class Award(models.Model):
    award_type = models.PositiveSmallIntegerField(choices=AwardType.choice_list)
    level = models.PositiveSmallIntegerField()
    account = models.ForeignKey(Account, related_name='awards')
    created = models.DateTimeField(default=timezone.now)

    objects = AwardManager()

    def __unicode__(self):
        return u'%s level %d award for %s' % (self.get_award_type_display(), self.level, self.account.username)

    def image_small(self):
        n = AwardType.name_for_value[self.award_type]
        return u'img/awards/award_%s_level_%d_50.png' % (n, self.level)

    def image_medium(self):
        n = AwardType.name_for_value[self.award_type]
        return u'img/awards/award_%s_level_%d_100.png' % (n, self.level)

    def short_description(self):
        return u'%s level %d' % (self.get_award_type_display(), self.level)

    def get_award_detail(self):
        return AWARD_CLASSES[self.award_type](level=self.level)

    def full_description(self):
        return self.get_award_detail().full_description()


import awards.hooks
