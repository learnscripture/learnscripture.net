from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from accounts.models import Account, SubscriptionType
from awards.signals import new_award
from scores.models import ScoreReason
from learnscripture.datastructures import make_choices

AwardType = make_choices('AwardType',
                         [(0, 'STUDENT', 'Student'),
                          (1, 'MASTER', 'Master'),
                          (2, 'SHARER', 'Sharer'),
                          (3, 'TREND_SETTER', 'Trend setter'),
                          (4, 'ACE', 'Ace'),
                          (5, 'RECRUITER', 'Recruiter'),
                          ])

# AnyLevel is used when displaying badges on the 'badges' page which describes
# badges in generic terms.
class AnyLevel(object):
    def __str__(self):
        return 'any'
AnyLevel = AnyLevel()

class AwardLogic(object):
    # Abstract base class for all classes that define behaviour for the types of
    # awards listed in AwardType

    # All subclasses need to define an __init__ that takes at least a 'level'
    # keyword argument.

    def slug(self):
        return AwardType.name_for_value[self.award_type].lower().replace('_', '-')

    def short_description(self):
        title = AwardType.titles[self.award_type]
        if self.level is AnyLevel:
            return title
        else:
            return u'%s - level %d' % (title, self.level)

    def image_small(self):
        n = AwardType.name_for_value[self.award_type]
        return u'img/awards/award_%s_level_%s_50.png' % (n, self.level)

    def image_medium(self):
        n = AwardType.name_for_value[self.award_type]
        return u'img/awards/award_%s_level_%s_100.png' % (n, self.level)

    def give_to(self, account):
        if self.level == 0:
            return
        if account.subscription == SubscriptionType.BASIC:
            return

        # Create lower levels if they don't exist because a higher level always
        # implies a lower level.

        existing_levels = (Award.objects.filter(account=account, award_type=self.award_type)
                           .values_list('level', flat=True))
        if len(existing_levels) < self.level:
            # Missing at least one
            missing_levels = set(range(1, self.level + 1)) - set(existing_levels)
            # Do lower levels first so notices are in right order
            missing_levels = sorted(list(missing_levels))
            for lev in missing_levels:
                award, new = Award.objects.get_or_create(account=account,
                                                         award_type=self.award_type,
                                                         level=lev)
                if new:
                    # Use a fresh instance in order to get the points
                    # calculation correct.
                    points = self.__class__(level=lev).points()
                    if points > 0:
                        account.add_points(points, ScoreReason.EARNED_AWARD)
                    new_award.send(sender=award, points=points)

    def points(self):
        return 0

    def highest_level(self):
        return Award.objects.filter(award_type=self.award_type).aggregate(models.Max('level'))['level__max']


class CountBasedAward(AwardLogic):

    # Subclass must define COUNTS, and optionally POINTS

    def __init__(self, level=None, count=None):
        """
        Must pass at least one of level or count
        """
        self._LEVELS_DESC = sorted([(a,b) for b, a in self.COUNTS.items()], reverse=True)
        if count is None:
            if level is AnyLevel:
                self.count = None
            else:
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

    def points(self):
        if hasattr(self, 'POINTS'):
            return self.POINTS[self.level]
        else:
            return 0


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
    POINTS = {1: 1000,
              2: 4000,
              3: 8000,
              4: 16000,
              5: 32000,
              6: 64000,
              7: 125000,
              8: 250000,
              9: 500000,
              }

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for starting to learn verses. Level 1 is for 1 verse, "\
                "going up to level 9 for the whole Bible."
        elif self.level == 1:
            return u"Learning at least one verse"
        elif self.level == 9:
            return u"Learning the whole bible!"
        else:
            return u"Learning at least %s verses" % self.count


class MasterAward(LearningAward):
    POINTS = dict((k, v*10) for k, v in StudentAward.POINTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for fully learning verses (5 stars). This takes about "\
                "a year, to make sure verses are really in there for good! "\
                "Level 1 is for 1 verse, "\
                "going up to level 9 for the whole Bible."
        elif self.level == 1:
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

    POINTS = dict((k, v*500) for k, v in COUNTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for creating public verse sets (selections)."\
                " Levels go from 1 for 1 verse set, level 5 for 20 verse sets."
        elif self.count == 1:
            return u"Created a public selection verse set"
        else:
            return u"Created %d public selection verse sets" % self.count


class TrendSetterAward(CountBasedAward):
    COUNTS = {1: 5,
              2: 10,
              3: 30,
              4: 100,
              5: 300,
              6: 1000,
              }

    POINTS = dict((k, v*500) for k, v in COUNTS.items())


    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for creating verse sets that other people actually use."\
                " Level 1 is given when 5 other people are using one of your verse sets."

        return u"Verse sets created by this user have been used by others at least %d times" % self.count


class AceAward(CountBasedAward):
    COUNTS = dict((k, 2**(k-1)) for k in range(1, 10))

    # counts are powers of 2, points are powers of 3, because achieving level n
    # + 1 is more than twice as hard as level n.
    POINTS = dict((k, 3**(k-1)*1000) for k in COUNTS.keys())

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for getting 100% in a test. Level 1 is for getting it once, "\
                "level 2 if you do it twice in a row, level 3 for 4 times in a row, "\
                "level 5 for 8 times in a row etc."

        if self.count == 1:
            return u"Achieved 100% in a test"
        else:
            return u"Achieved 100%% in a test %d times in a row" % self.count


class RecruiterAward(CountBasedAward):
    COUNTS = {1: 1,
              2: 3,
              3: 5,
              4: 10,
              5: 15,
              6: 20,
              7: 25,
              8: 30,
              9: 50,
              }
    POINTS = dict((k, v*10000) for (k,v) in COUNTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for getting other people to sign up using our referral programme. "\
                "This award is actually worth money! (If referrals become paying members, that is). "\
                "Level 1 is for one referral, and is with 10,000 points."
        elif self.count == 1:
            return "Got one person to sign up to LearnScripture.net through our referral programme"
        else:
            return "Got %d people to sign up to LearnScripture.net through our referral programme" % self.count

AWARD_CLASSES = {
    AwardType.STUDENT: StudentAward,
    AwardType.MASTER: MasterAward,
    AwardType.SHARER: SharerAward,
    AwardType.TREND_SETTER: TrendSetterAward,
    AwardType.ACE: AceAward,
    AwardType.RECRUITER: RecruiterAward,
}

for t, c in AWARD_CLASSES.items():
    c.award_type = t


class Award(models.Model):
    award_type = models.PositiveSmallIntegerField(choices=AwardType.choice_list)
    level = models.PositiveSmallIntegerField()
    account = models.ForeignKey(Account, related_name='awards')
    created = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u'%s level %d award for %s' % (self.get_award_type_display(), self.level, self.account.username)

    @cached_property
    def award_detail(self):
        return AWARD_CLASSES[self.award_type](level=self.level)

    def image_small(self):
        return self.award_detail.image_small()

    def image_medium(self):
        return self.award_detail.image_medium()

    def short_description(self):
        return self.award_detail.short_description()

    def full_description(self):
        return self.award_detail.full_description()


import awards.hooks
