from django.db import models
from django.utils import timezone

from accounts.models import Account
from learnscripture.datastructures import make_choices

AwardType = make_choices('AwardType',
                         [(0, 'STUDENT', 'Student'),
                          ])


class Award(models.Model):
    award_type = models.PositiveSmallIntegerField(choices=AwardType.choice_list)
    level = models.PositiveSmallIntegerField()
    account = models.ForeignKey(Account, related_name='awards')
    created = models.DateTimeField(default=timezone.now)


    def __unicode__(self):
        return u'%s level %d award for %s' % (self.level, self.get_award_type_display(), self.account.username)

    def image_medium(self):
        n = AwardType.name_for_value[self.award_type]
        return u'img/awards/award_%s_level_%d_100.png' % (n, self.level)

    def short_description(self):
        return u'%s level %d' % (self.get_award_type_display(), self.level)

    def full_description(self):
        if self.award_type == AwardType.STUDENT:
            counts = {1: 1,
                      2: 10,
                      3: 30,
                      4: 100,
                      5: 300,
                      6: 1000,
                      7: 3000,
                      8: 10000,
                      9: 31102, # every verse
                      }
            if self.level == 1:
                return u"Learning at least one verse"
            else:
                return u"Learning at least %s verses" % counts[self.level]
