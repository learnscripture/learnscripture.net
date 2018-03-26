from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html

from accounts.models import Account
from awards.signals import new_award
from learnscripture.datastructures import make_class_enum
from scores.models import ScoreReason


# In this module we have:
#
# = AwardType =
#
# Class storing enumeration of the different award types,
# including a mapping of enumeration value to an AwardLogic subclass
#
# = AwardLogic and subclasses =
#
# Classes holding details about individual types of awards, and the
# levels/counts/points they have. It contains some utility methods.
#
# The queries needed to calculate counts are not contained in the AwardLogic
# classes, but in awards.tasks and other places.
#
# = Award model =
#
# Stores info in DB, including 'level' and 'award_type'. It has a number of
# methods/properties that proxy to an instance of the relevant AwardLogic
# subclass.


# AnyLevel is used when displaying badges on the 'badges' page which describes
# badges in generic terms.
class AnyLevel(object):
    def __str__(self):
        return 'any'


AnyLevel = AnyLevel()


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class AwardLogic(object):
    # Abstract base class for all classes that define behaviour for the types of
    # awards listed in AwardType

    # All subclasses need to define an __init__ that takes at least a 'level'
    # keyword argument.

    # Subclasses must also define 'has_levels' class attribute and 'max_level'
    # attribute

    removed = False

    @classproperty
    @classmethod
    def award_type(cls):
        return cls.enum_val  # set by make_class_enum

    @classmethod
    def slug(cls):
        return AwardType.name_for_value[cls.award_type].lower().replace('_', '-')

    @classproperty
    @classmethod
    def title(cls):
        return AwardType.titles[cls.award_type]

    def short_description(self):
        if self.level is AnyLevel:
            return self.title
        else:
            if self.has_levels:
                return '%s - level %d' % (self.title, self.level)
            else:
                return self.title

    def image_small(self):
        n = AwardType.name_for_value[self.award_type]
        return 'img/awards/award_%s_level_%s_50.png' % (n, self.level)

    def image_medium(self):
        n = AwardType.name_for_value[self.award_type]
        return 'img/awards/award_%s_level_%s_100.png' % (n, self.level)

    def give_to(self, account):
        if self.level == 0:
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
                        account.add_points(points, ScoreReason.EARNED_AWARD, award=award)
                    new_award.send(sender=award, points=points)

    def points(self):
        return 0

    @cached_property
    def highest_level_achieved(self):
        """
        The highest level that has been achieved
        """
        return Award.objects.filter(award_type=self.award_type,
                                    account__is_active=True,
                                    account__is_hellbanned=False,
                                    )\
            .aggregate(models.Max('level'))['level__max']


class MultiLevelPointsMixin(object):
    def points(self):
        if hasattr(self, 'POINTS'):
            return self.POINTS[self.level]
        else:
            return 0


class CountBasedAward(MultiLevelPointsMixin, AwardLogic):
    """
    Base class for awards that have different levels that are based on
    a 'count' of some kind.
    """
    # Subclasses must define COUNTS and POINTS as class attributes, as
    # dictionaries mapping level to count and level to points respectively.

    has_levels = True

    @classproperty
    @classmethod
    def max_level(cls):
        return max(cls.COUNTS.keys())

    # Subclass must define COUNTS, and optionally POINTS

    def __init__(self, level=None, count=None):
        """
        Must pass at least one of level or count
        """
        self._LEVELS_DESC = sorted([(a, b) for b, a in self.COUNTS.items()], reverse=True)
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


class SingleLevelAward(AwardLogic):
    """
    Base class for awards that do not have multiple levels
    """
    # Subclasses should define:
    #  POINTS (integer)

    has_levels = False

    max_level = 1

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
              9: 31102,  # every verse
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
            return "Learning at least one verse"
        elif self.level == 9:
            return "Learning the whole bible!"
        else:
            return "Learning at least %s verses" % self.count


class MasterAward(LearningAward):
    POINTS = dict((k, v * 10) for k, v in StudentAward.POINTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for fully learning verses (5 stars). This takes about "\
                "a year, to make sure verses are really in there for good! "\
                "Level 1 is for 1 verse, "\
                "going up to level 9 for the whole Bible."
        elif self.level == 1:
            return "Finished learning at least one verse"
        elif self.level == 9:
            return "Finished learning the whole bible!"
        else:
            return "Finished learning at least %s verses" % self.count


class SharerAward(CountBasedAward):
    COUNTS = {1: 1,
              2: 2,
              3: 5,
              4: 10,
              5: 20,
              }

    POINTS = dict((k, v * 500) for k, v in COUNTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for creating public verse sets (selections)."\
                " Levels go from 1 for 1 verse set, to level 5 for 20 verse sets."
        elif self.count == 1:
            return "Created a public selection verse set"
        else:
            return "Created %d public selection verse sets" % self.count


class TrendSetterAward(CountBasedAward):
    COUNTS = {1: 5,
              2: 10,
              3: 30,
              4: 100,
              5: 300,
              6: 1000,
              }

    POINTS = dict((k, v * 500) for k, v in COUNTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for creating verse sets that other people actually use."\
                " Level 1 is given when 5 other people are using one of your verse sets."

        return "Verse sets created by this user have been used by others at least %d times" % self.count


class AceAward(CountBasedAward):
    COUNTS = {k: 2 ** (k - 1) for k in range(1, 10)}

    POINTS = {k: v * 1000 for k, v in COUNTS.items()}

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for getting 100% in a test. Level 1 is for getting it once, "\
                "level 2 if you do it twice in a row, level 3 for 4 times in a row, "\
                "level 4 for 8 times in a row etc."

        if self.count == 1:
            return "Achieved 100% in a test"
        else:
            return "Achieved 100%% in a test %d times in a row" % self.count


class RecruiterAward(CountBasedAward):
    COUNTS = {1: 1,
              2: 2,
              3: 3,
              4: 5,
              5: 10,
              6: 15,
              7: 20,
              8: 30,
              9: 50,
              }
    POINTS = dict((k, v * 20000) for (k, v) in COUNTS.items())

    def full_description(self):
        url = reverse('referral_program')
        if self.level is AnyLevel:
            return format_html("Awarded for getting other people to sign up using our "
                               "<a href='{0}'>referral program</a>. "
                               "Level 1 is for one referral, and is worth 20,000 points.",
                               url)
        elif self.count == 1:
            return format_html("Got one person to sign up to LearnScripture.net "
                               "through our <a href='{0}'>referral program</a>",
                               url)
        else:
            return format_html("Got {0} people to sign up to LearnScripture.net "
                               "through our <a href='{1}'>referral program</a>",
                               self.count, url)


class HackerAward(SingleLevelAward):
    POINTS = 0

    def full_description(self):
        return ("Awarded to leet hackers who find some bug in the site that allows you to cheat. "
                "This award comes with the risk of getting your points reset to zero and/or being kicked out :-)")


class ReigningWeeklyChampion(SingleLevelAward):
    removed = True
    POINTS = 0


class TimeBasedAward(MultiLevelPointsMixin, AwardLogic):
    """
    Subclasses must define:
    DAYS: dictionary mapping level to number of days

    Also useful:
    FRIENDLY_DAYS: dictionary mapping level to string indicating number of days.
    """

    has_levels = True

    @classproperty
    @classmethod
    def max_level(cls):
        return max(cls.DAYS.keys())

    def __init__(self, level=None, time_period=None):
        if level is None:
            self.level = self.level_for_time_period(time_period)
        else:
            self.level = level

    def level_for_time_period(self, time_period):
        # period is a timedelta object
        _DAYS_DESC = sorted([(a, b) for b, a in self.DAYS.items()], reverse=True)

        for d, level in _DAYS_DESC:
            if time_period.days >= d:
                return level
        return 0


class WeeklyChampion(AwardLogic):
    removed = True
    has_levels = True

    def __init__(self, level=None):
        self.level = level


class AddictAward(SingleLevelAward):
    POINTS = 10000

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded to users who've done verse tests during every hour on the clock."
        else:
            return "Done verse tests during every hour on the clock"


class OrganizerAward(CountBasedAward):
    COUNTS = {1: 5,
              2: 10,
              3: 20,
              4: 50,
              5: 100,
              }

    POINTS = dict((k, v * 500) for k, v in COUNTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return "Awarded for getting people to together in groups. First level "\
                "requires 5 people to join one of your groups."
        else:
            return "Created groups that are used by at least %d people" % self.count


class ConsistentLearnerAward(TimeBasedAward):

    POINTS = dict((l, v * 4) for l, v in StudentAward.POINTS.items())

    DAYS = {
        1: 7,
        2: 14,
        3: 31,
        4: 91,
        5: 182,
        6: 274,
        7: 365,
        8: 547,
        9: 730,
    }

    FRIENDLY_DAYS = {
        1: '1 week',
        2: '2 weeks',
        3: '1 month',
        4: '3 months',
        5: '6 months',
        6: '9 months',
        7: '1 year',
        8: '18 months',
        9: '2 years'
    }

    def full_description(self):
        if self.level is AnyLevel:
            return ("Awarded for starting to learn a new verse every day without gaps, "
                    "over a period of time. Note that you have to keep learning the verses "
                    "for them to be counted. Days are defined by the UTC time zone."
                    " Level 1 is for 1 week, level 9 is for 2 years.")
        else:
            return "Started learning a new verse every day for %s" % self.FRIENDLY_DAYS[self.level]


AwardType = make_class_enum(
    'AwardType',
    [('STUDENT', 'Student', StudentAward),
     ('MASTER', 'Master', MasterAward),
     ('SHARER', 'Sharer', SharerAward),
     ('TREND_SETTER', 'Trend setter', TrendSetterAward),
     ('ACE', 'Ace', AceAward),
     ('RECRUITER', 'Recruiter', RecruiterAward),
     ('HACKER', 'Hacker', HackerAward),
     ('WEEKLY_CHAMPION', 'Weekly champion', WeeklyChampion),  # Removed
     ('REIGNING_WEEKLY_CHAMPION', 'Reigning weekly champion', ReigningWeeklyChampion),  # Removed
     ('ADDICT', 'Addict', AddictAward),
     ('ORGANIZER', 'Organizer', OrganizerAward),
     ('CONSISTENT_LEARNER', 'Consistent learner', ConsistentLearnerAward),
     ])


class Award(models.Model):
    award_type = models.CharField(max_length=40, choices=AwardType.choice_list)
    level = models.PositiveSmallIntegerField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE,
                                related_name='awards')
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '%s level %d award for %s' % (self.get_award_type_display(), self.level, self.account.username)

    @property
    def award_class(self):
        return AwardType.classes[self.award_type]

    @cached_property
    def award_detail(self):
        return self.award_class(level=self.level)

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
