from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.safestring import mark_safe

from accounts.models import Account, SubscriptionType
from awards.signals import new_award
from scores.models import ScoreReason
from learnscripture.datastructures import make_choices

# In this module we have:
#
# = AwardType =
#
# Class storing enumeration of the different award types
#
# = AwardLogic and subclasses =
#
# Classes holding details about individual types of awards, and the
# levels/counts/points they have. It contains some utility methd
#
# The queries needed to calculate counts are not contained in the AwardLogic
# classes, but in awards.tasks and other places.
#
# This is mapped to AwardType using a simple dictionary AWARD_CLASSES
#
# = Award model =
#
# Stores info in DB, including 'level' and 'award_type'. It has a number of
# methods/properties that proxy to an instance of the relevant AwardLogic
# subclass.

AwardType = make_choices('AwardType',
                         [(0, 'STUDENT', u'Student'),
                          (1, 'MASTER', u'Master'),
                          (2, 'SHARER', u'Sharer'),
                          (3, 'TREND_SETTER', u'Trend setter'),
                          (4, 'ACE', u'Ace'),
                          (5, 'RECRUITER', u'Recruiter'),
                          (6, 'HACKER', u'Hacker'),
                          (7, 'WEEKLY_CHAMPION', u'Weekly champion'),
                          (8, 'REIGNING_WEEKLY_CHAMPION', u'Reigning weekly champion'),
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

    # Subclasses must also define 'has_levels' class attribute

    def slug(self):
        return AwardType.name_for_value[self.award_type].lower().replace(u'_', u'-')

    def short_description(self):
        title = AwardType.titles[self.award_type]
        if self.level is AnyLevel:
            return title
        else:
            if self.has_levels:
                return u'%s - level %d' % (title, self.level)
            else:
                return title

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
    """
    Base class for awards that have different levels that are based on
    a 'count' of some kind.
    """
    has_levels = True


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


class SingleLevelAward(AwardLogic):
    """
    Base class for awards that do not have multiple levels
    """
    # Subclasses should define:
    #  POINTS (integer)

    has_levels = False

    def __init__(self, level=1):
        self.level = level

    def points(self):
        return self.POINTS


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
                " Levels go from 1 for 1 verse set, to level 5 for 20 verse sets."
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
                "level 4 for 8 times in a row etc."

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
    POINTS = dict((k, v*20000) for (k,v) in COUNTS.items())

    def full_description(self):
        url = reverse('referral_program')
        if self.level is AnyLevel:
            return mark_safe(u"Awarded for getting other people to sign up using our "
                             "<a href='%s'>referral program</a>. "
                             "This award is actually worth money! (If referrals become "
                             "paying members, that is). "
                             "Level 1 is for one referral, and is worth 20,000 points." %
                             escape(url))
        elif self.count == 1:
            return mark_safe(u"Got one person to sign up to LearnScripture.net "
                             "through our <a href='%s'>referral program</a>" %
                             escape(url))
        else:
            return mark_safe(u"Got %d people to sign up to LearnScripture.net "
                             "through our <a href='%s'>referral program</a>" %
                             (self.count, escape(url)))


class HackerAward(SingleLevelAward):
    POINTS = 0

    def full_description(self):
        return u"Awarded to leet hackers who find some bug in the site that allows you to cheat. "\
        "This award comes with the risk of getting your points reset to zero and/or being kicked out :-)"


class ReigningWeeklyChampion(SingleLevelAward):
    POINTS = 0

    def full_description(self):
        url = reverse('leaderboard') + "?thisweek"
        if self.level is AnyLevel:
            return mark_safe(u'Awarded to the user who is currently at the top of the <a href="%s">weekly leaderboard</a>.' % url)
        else:
            return mark_safe(u'Currently at the top of the <a href="%s">weekly leaderboard</a>.' % url)


class WeeklyChampion(AwardLogic):

    has_levels = True


    DAYS = {
        1: 0, # less than a day
        2: 1, # 1 day
        3: 7,
        4: 14,
        5: 30,
        6: 91,
        7: 182,
        8: 274,
        9: 365,
        }
    FRIENDLY_DAYS = {
        1: '',
        2: '1 day',
        3: '1 week',
        4: '2 weeks',
        5: '1 month',
        6: '3 months',
        7: '6 months',
        8: '9 months',
        9: '1 year',
        }

    def __init__(self, level=None, time_period=None):
        if level is None:
            self.level = self.level_for_time_period(time_period)
        else:
            self.level = level

    def level_for_time_period(self, time_period):
        # period is a timedelta object
        _DAYS_DESC = sorted([(a,b) for b, a in self.DAYS.items()], reverse=True)

        for d, level in _DAYS_DESC:
            if time_period.days >= d:
                return level
        return 0

    def full_description(self):
        url = reverse('leaderboard') + "?thisweek"
        if self.level is AnyLevel:
            return mark_safe(u'Awarded to all users who have reached the top of the <a href="%s">weekly leaderboard</a>.  Higher levels are achieved by staying there longer, up to level 9 if you stay there for a year.' % url)
        else:
            d = u'Reached the top of the <a href="%s">weekly leaderboard</a>' % url
            if self.level > 1:
                d = d + ", and stayed there for at least %s" % self.FRIENDLY_DAYS[self.level]
            return mark_safe(d)

AWARD_CLASSES = {
    AwardType.STUDENT: StudentAward,
    AwardType.MASTER: MasterAward,
    AwardType.SHARER: SharerAward,
    AwardType.TREND_SETTER: TrendSetterAward,
    AwardType.ACE: AceAward,
    AwardType.RECRUITER: RecruiterAward,
    AwardType.HACKER: HackerAward,
    AwardType.REIGNING_WEEKLY_CHAMPION: ReigningWeeklyChampion,
    AwardType.WEEKLY_CHAMPION: WeeklyChampion,
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

    def has_levels(self):
        return self.award_detail.has_levels

    def delete(self, **kwargs):
        from awards.signals import lost_award
        lost_award.send(sender=self)
        return super(Award, self).delete(**kwargs)

import awards.hooks
