from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from accounts.models import Account
from awards.signals import new_award
from learnscripture.ftl_bundles import t, t_lazy
from learnscripture.utils.introspection import all_subclasses
from scores.models import ScoreReason

# In this module we have:
#
# = AwardType =
#
# Class storing enumeration of the different award types
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


class AwardType(models.TextChoices):
    STUDENT = 'STUDENT', t_lazy('awards-student-award-name')
    MASTER = 'MASTER', t_lazy('awards-master-award-name')
    SHARER = 'SHARER', t_lazy('awards-sharer-award-name')
    TREND_SETTER = 'TREND_SETTER', t_lazy('awards-trend-setter-award-name')
    ACE = 'ACE', t_lazy('awards-ace-award-name')
    RECRUITER = 'RECRUITER', t_lazy('awards-recruiter-award-name')
    WEEKLY_CHAMPION = 'WEEKLY_CHAMPION', 'Weekly champion'  # Removed
    REIGNING_WEEKLY_CHAMPION = 'REIGNING_WEEKLY_CHAMPION', 'Reigning weekly champion'  # Removed
    ADDICT = 'ADDICT', t_lazy('awards-addict-award-name')
    ORGANIZER = 'ORGANIZER', t_lazy('awards-organizer-award-name')
    CONSISTENT_LEARNER = 'CONSISTENT_LEARNER', t_lazy('awards-consistent-learner-award-name')


class AwardLogic(object):
    # Abstract base class for all classes that define behaviour for the types of
    # awards listed in AwardType

    # Subclasses must defined award_type

    # All subclasses need to define an __init__ that takes at least a 'level'
    # keyword argument.

    # Subclasses must also define 'has_levels' class attribute and 'max_level'
    # attribute

    award_type = NotImplemented
    removed = False

    @classmethod
    def slug(cls):
        return cls.award_type.value.lower().replace('_', '-')

    @classproperty
    @classmethod
    def title(cls):
        return cls.award_type.label

    def short_description(self):
        if self.level is AnyLevel:
            return str(self.title)
        else:
            if self.has_levels:
                return t('awards-level-title',
                         dict(name=str(self.title), level=self.level))
            else:
                return str(self.title)

    def image_small(self):
        n = self.award_type.name
        return f'img/awards/award_{n}_level_{self.level}_50.png'

    def image_medium(self):
        n = self.award_type.name
        return f'img/awards/award_{n}_level_{self.level}_100.png'

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
    award_type = AwardType.STUDENT
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
            return t('awards-student-award-general-description')
        if self.level == 9:
            return t('awards-student-award-level-9-description')
        return t('awards-student-award-level-n-description', dict(verse_count=self.count))


class MasterAward(LearningAward):
    award_type = AwardType.MASTER
    POINTS = dict((k, v * 10) for k, v in StudentAward.POINTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return t('awards-master-award-general-description')
        if self.level == 9:
            return t('awards-master-award-level-9-description')
        return t('awards-master-award-level-n-description', dict(verse_count=self.count))


class SharerAward(CountBasedAward):
    award_type = AwardType.SHARER
    COUNTS = {1: 1,
              2: 2,
              3: 5,
              4: 10,
              5: 20,
              }

    POINTS = dict((k, v * 500) for k, v in COUNTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return t('awards-sharer-award-general-description')
        return t('awards-sharer-award-level-n-description', dict(count=self.count))


class TrendSetterAward(CountBasedAward):
    award_type = AwardType.TREND_SETTER
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
            return t('awards-trend-setter-award-level-general-description')

        return t('awards-trend-setter-award-level-n-description', dict(count=self.count))


class AceAward(CountBasedAward):
    award_type = AwardType.ACE
    COUNTS = {k: 2 ** (k - 1) for k in range(1, 10)}

    POINTS = {k: v * 1000 for k, v in COUNTS.items()}

    def full_description(self):
        if self.level is AnyLevel:
            return t('awards-ace-award-general-description')

        if self.count == 1:
            return t('awards-ace-award-level-1-description')
        else:
            return t('awards-ace-award-level-n-description',
                     dict(count=self.count))


class RecruiterAward(CountBasedAward):
    award_type = AwardType.RECRUITER
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
            return t('awards-recruiter-award-general-description-html',
                     dict(url=url))
        return t('awards-recruiter-award-level-n-description-html',
                 dict(url=url, count=self.count))


class ReigningWeeklyChampion(SingleLevelAward):
    award_type = AwardType.REIGNING_WEEKLY_CHAMPION
    removed = True
    POINTS = 0


class TimeBasedAward(MultiLevelPointsMixin, AwardLogic):
    """
    Subclasses must define:
    DAYS: dictionary mapping level to number of days
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
    award_type = AwardType.WEEKLY_CHAMPION
    removed = True
    has_levels = True

    def __init__(self, level=None):
        self.level = level


class AddictAward(SingleLevelAward):
    award_type = AwardType.ADDICT
    POINTS = 10000

    def full_description(self):
        if self.level is AnyLevel:
            return t('awards-addict-award-general-description')
        else:
            return t('awards-addict-award-level-all-description')


class OrganizerAward(CountBasedAward):
    award_type = AwardType.ORGANIZER
    COUNTS = {1: 5,
              2: 10,
              3: 20,
              4: 50,
              5: 100,
              }

    POINTS = dict((k, v * 500) for k, v in COUNTS.items())

    def full_description(self):
        if self.level is AnyLevel:
            return t('awards-organizer-award-general-description')
        else:
            return t('awards-organizer-award-level-n-description', dict(count=self.count))


class ConsistentLearnerAward(TimeBasedAward):
    award_type = AwardType.CONSISTENT_LEARNER
    POINTS = dict((level, points * 4) for level, points in StudentAward.POINTS.items())

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
        10: 1095,
    }

    def full_description(self):
        if self.level is AnyLevel:
            return t('awards-consistent-learner-award-general-description')
        else:
            # awards-consistent-learner-award-level-1-description etc
            return t(f'awards-consistent-learner-award-level-{self.level}-description')


AWARD_LOGIC_CLASSES = {
    cls.award_type: cls
    for cls in all_subclasses(AwardLogic)
    if getattr(cls, 'award_type') != NotImplemented
}


class Award(models.Model):
    award_type = models.CharField(max_length=40, choices=AwardType.choices)
    level = models.PositiveSmallIntegerField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE,
                                related_name='awards')
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return t('awards-level-awarded-for-user',
                 dict(award_name=str(self.get_award_type_display()),
                      award_level=self.level,
                      username=self.account.username))

    @property
    def award_class(self):
        return AWARD_LOGIC_CLASSES[self.award_type]

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
