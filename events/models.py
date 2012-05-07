from datetime import timedelta
import math

from django.db import models
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.html import escape
from jsonfield import JSONField

from learnscripture.datastructures import make_choices


EVENTSTREAM_CUTOFF_DAYS = 3 # just 3 days of events
EVENTSTREAM_CUTOFF_NUMBER = 8

# Arbitrarily say stuff is 50% less interesting when it is one day old.
EVENTSTREAM_TIME_DECAY_FACTOR = 3600*24

# This means that with EVENTSTREAM_CUTOFF_DAYS = 3, there is a factor of 8 to
# play with: if an event has a weight more than 8 times higher than the rest of
# the stream, it will stay at the top of the event stream until it disappears
# altogether.


EventType = make_choices('EventType',
                         [(1, 'NOTICE', 'Notice'),
                          (2, 'NEW_ACCOUNT', 'New account'),
                          (3, 'AWARD_RECEIVED', 'Award received'),
                          (4, 'POINTS_MILESTONE', 'Points milestone'),
                          (5, 'VERSES_STARTED_MILESTONE', 'Verses started milestone'),
                          (6, 'VERSES_FINISHED_MILESTONE', 'Verses finished milestone'),
                          (7, 'VERSE_SET_CREATED', 'Verse set created'),
                          (8, 'STARTED_LEARNING_VERSE_SET', 'Started learning a verse set'),
                          ])


class EventLogic(object):

    weight = 10

    def __init__(self, **kwargs):
        """
        Initialises EventLogic and an Event instance.

        kwargs can be:
         - message_html - passed on to Event()
         - anything else - stored in Event.event_data,
           so must be simple types that can be serialised to JSON.
        """
        self.event_data = kwargs
        message_html = kwargs.pop('message_html', '')
        self.event = Event(weight=self.weight,
                           event_type=self.event_type,
                           message_html=message_html)

    def save(self):
        self.event.event_data = self.event_data
        self.event.save()


class NoticeEvent(EventLogic):
    """
    Events used to broadcast notices to all users.
    """
    weight = EventLogic.weight * 3


def account_url(account):
    return reverse('user_stats', args=(account.username,))


class NewAccountEvent(EventLogic):

    def __init__(self, account=None):
        super(NewAccountEvent, self).__init__(account_id=account.id)
        extra_name = ""
        if account.first_name.strip() != "":
            extra_name = account.first_name.strip()
        if account.last_name.strip() != "":
            extra_name += " " + account.last_name.strip()
        extra_name = extra_name.strip()
        if extra_name != "":
            extra_name = "(%s)" % extra_name
        self.event.message_html = ("<a href='%s'>%s</a> %s signed up to LearnScripture.net" %
                                   tuple(map(escape,
                                             [account_url(account),
                                              account.username,
                                              extra_name]))
                                   )


class AwardReceivedEvent(EventLogic):

    # Awards are quite interesting
    weight = EventLogic.weight * 2

    def __init__(self, award=None):
        super(AwardReceivedEvent, self).__init__(award_id=award.id)
        self.event.message_html = (
            "<a href='%s'>%s</a> received <b>%s</b> award"
            % tuple(map(escape,
                        [account_url(award.account),
                         award.account.username,
                         award.short_description()]))
            )


class VerseSetCreatedEvent(EventLogic):

    def __init__(self, verse_set=None):
        super(VerseSetCreatedEvent, self).__init__(verse_set_id=verse_set.id)
        self.event.message_html = (
            'New verse set <a href="%s">%s</a> created by <a href="%s">%s</a>' %
            tuple(map(escape,
                      [reverse('view_verse_set', args=(verse_set.slug,)),
                       verse_set.name,
                       account_url(verse_set.created_by),
                       verse_set.created_by.username,
                       ]))
            )


class StartedLearningVerseSetEvent(EventLogic):
    def __init__(self, verse_set=None, chosen_by=None):
        super(StartedLearningVerseSetEvent, self).__init__(verse_set_id=verse_set.id,
                                                           chosen_by_id=chosen_by.id)
        self.event.message_html = (
            '<a href="%s">%s</a> started learning <a href="%s">%s</a>' %
            tuple(map(escape,
                      [account_url(chosen_by),
                       chosen_by.username,
                       reverse('view_verse_set', args=(verse_set.slug,)),
                       verse_set.name,
                       ]))
            )


class PointsMilestoneEvent(EventLogic):
    def __init__(self, account=None, points=None):
        super(PointsMilestoneEvent, self).__init__(account_id=account.id,
                                                   points=points)
        self.event.message_html = (
            '<a href="%s">%s</a> reached %s points' %
            tuple(map(escape,
                      [account_url(account),
                       account.username,
                       intcomma(points)]))
            )


class VersesStartedMilestoneEvent(EventLogic):
    def __init__(self, account=None, verses_started=None):
        super(VersesStartedMilestoneEvent, self).__init__(account_id=account.id,
                                                          verses_started=verses_started)
        self.event.message_html = (
            '<a href="%s">%s</a> reached %s verses started' %
            tuple(map(escape,
                      [account_url(account),
                       account.username,
                       intcomma(verses_started)]))
            )


EVENT_CLASSES = {
    EventType.NEW_ACCOUNT: NewAccountEvent,
    EventType.AWARD_RECEIVED: AwardReceivedEvent,
    EventType.POINTS_MILESTONE: PointsMilestoneEvent,
    EventType.VERSES_STARTED_MILESTONE: VersesStartedMilestoneEvent,
    EventType.VERSE_SET_CREATED: VerseSetCreatedEvent,
    EventType.STARTED_LEARNING_VERSE_SET: StartedLearningVerseSetEvent,
}


for event_type, c in EVENT_CLASSES.items():
    c.event_type = event_type


class EventManager(models.Manager):
    def for_dashboard(self, now=None):
        if now is None:
            now = timezone.now()

        start = now - timedelta(EVENTSTREAM_CUTOFF_DAYS)
        events = list(self.filter(created__gte=start))
        events.sort(key=lambda e: e.get_rank(), reverse=True)
        return events[0:EVENTSTREAM_CUTOFF_NUMBER]


class Event(models.Model):
    message_html = models.TextField()
    event_type = models.PositiveSmallIntegerField(choices=EventType.choice_list)
    weight = models.PositiveSmallIntegerField(default=10)
    event_data = JSONField(blank=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)

    objects = EventManager()

    def __unicode__(self):
        return "Event %d" % self.id

    def get_rank(self, now=None):
        # In the future, we will want to include affinities in ranking, and will
        # need UserEvent or something, but for now just use weight and recency.

        if now is None:
            now = timezone.now()

        seconds = (now - self.created).total_seconds()

        recency = 2 ** (-seconds/EVENTSTREAM_TIME_DECAY_FACTOR)
        return self.weight * recency


    def created_display(self):
        from django.utils.timesince import timesince
        now = timezone.now()
        diff = now - self.created
        if diff.total_seconds() < 60:
            return u"Just now"
        return timesince(self.created, now=now) + " ago"

import events.hooks
