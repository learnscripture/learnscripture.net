from datetime import timedelta
import itertools
import math

from django.db import models
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from jsonfield import JSONField

from accounts.models import Account
from groups.utils import group_link
from learnscripture.datastructures import make_choices
from learnscripture.templatetags.account_utils import account_link


EVENTSTREAM_CUTOFF_DAYS = 3 # just 3 days of events
EVENTSTREAM_CUTOFF_NUMBER = 8

# Arbitrarily say stuff is 50% less interesting when it is half a day old.
EVENTSTREAM_TIME_DECAY_FACTOR = 3600*12.0

# This means that with EVENTSTREAM_CUTOFF_DAYS = 3, there is a factor of 8 to
# play with: if an event has a weight more than 8 times higher than the rest of
# the stream, it will stay at the top of the event stream until it disappears
# altogether.


EventType = make_choices('EventType',
                         [(2, 'NEW_ACCOUNT', 'New account'),
                          (3, 'AWARD_RECEIVED', 'Award received'),
                          (4, 'POINTS_MILESTONE', 'Points milestone'),
                          (5, 'VERSES_STARTED_MILESTONE', 'Verses started milestone'),
                          (6, 'VERSES_FINISHED_MILESTONE', 'Verses finished milestone'),
                          (7, 'VERSE_SET_CREATED', 'Verse set created'),
                          (8, 'STARTED_LEARNING_VERSE_SET', 'Started learning a verse set'),
                          (9, 'AWARD_LOST', 'Award lost'),
                          (10, 'GROUP_JOINED', 'Group joined'),
                          (11, 'GROUP_CREATED', 'Group created'),
                          ])


class EventLogic(object):

    weight = 10

    def __init__(self, **kwargs):
        """
        Initialises EventLogic and an Event instance.

        kwargs can be:
         - account - passed on to Event()
         - message_html - passed on to Event()
         - anything else - stored in Event.event_data,
           so must be simple types that can be serialised to JSON.
        """
        account = kwargs.pop('account', None)
        message_html = kwargs.pop('message_html', '')
        self.event_data = kwargs
        self.event = Event(weight=self.weight,
                           event_type=self.event_type,
                           message_html=message_html,
                           account=account)

    def save(self):
        self.event.event_data = self.event_data
        self.event.save()


class NewAccountEvent(EventLogic):

    def __init__(self, account=None):
        super(NewAccountEvent, self).__init__(account=account)
        extra_name = ""
        if account.first_name.strip() != "":
            extra_name = account.first_name.strip()
        if account.last_name.strip() != "":
            extra_name += " " + account.last_name.strip()
        extra_name = extra_name.strip()
        if extra_name != "":
            extra_name = "(%s)" % extra_name
        self.event.message_html = ("%s signed up to LearnScripture.net" %
                                   escape(extra_name))


class AwardReceivedEvent(EventLogic):

    # Awards are quite interesting
    weight = 12

    def __init__(self, award=None):
        super(AwardReceivedEvent, self).__init__(award_id=award.id,
                                                 account=award.account)
        self.event.message_html = (
            "earned <b>%s</b>" % escape(award.short_description())
            )


class AwardLostEvent(EventLogic):

    weight = AwardReceivedEvent.weight

    def __init__(self, award=None):
        super(AwardLostEvent, self).__init__(award_id=award.id,
                                             account=award.account)
        self.event.message_html = (
            "lost <a href='%s'>%s</a>" %
            tuple(map(escape,
                      [reverse('award', args=(award.award_detail.slug(),)),
                       award.short_description()
                       ]))
            )


class VerseSetCreatedEvent(EventLogic):

    def __init__(self, verse_set=None):
        super(VerseSetCreatedEvent, self).__init__(verse_set_id=verse_set.id,
                                                   account=verse_set.created_by)
        self.event.message_html = (
            'created new verse set <a href="%s">%s</a>' %
            tuple(map(escape,
                      [reverse('view_verse_set', args=(verse_set.slug,)),
                       verse_set.name,
                       ]))
            )


class StartedLearningVerseSetEvent(EventLogic):

    weight = 13

    def __init__(self, verse_set=None, chosen_by=None):
        super(StartedLearningVerseSetEvent, self).__init__(verse_set_id=verse_set.id,
                                                           account=chosen_by)
        self.event.message_html = (
            'started learning <a href="%s">%s</a>' %
            tuple(map(escape,
                      [reverse('view_verse_set', args=(verse_set.slug,)),
                       verse_set.name,
                       ]))
            )


class PointsMilestoneEvent(EventLogic):
    def __init__(self, account=None, points=None):
        super(PointsMilestoneEvent, self).__init__(account=account,
                                                   points=points)
        self.event.message_html = (
            'reached %s points' % escape(intcomma(points))
            )


class VersesStartedMilestoneEvent(EventLogic):
    def __init__(self, account=None, verses_started=None):
        super(VersesStartedMilestoneEvent, self).__init__(account=account,
                                                          verses_started=verses_started)
        self.event.message_html = (
            'reached %s verses started' % escape(intcomma(verses_started))
            )


class GroupJoinedEvent(EventLogic):

    def __init__(self, account=None, group=None):
        super(GroupJoinedEvent, self).__init__(account=account,
                                               group_id=group.id)

        self.event.message_html = u"joined group %s" % group_link(group)


class GroupCreatedEvent(EventLogic):

    def __init__(self, account=None, group=None):
        super(GroupCreatedEvent, self).__init__(account=account,
                                                group_id=group.id)
        self.event.message_html = u"created group %s" % group_link(group)


EVENT_CLASSES = {
    EventType.NEW_ACCOUNT: NewAccountEvent,
    EventType.AWARD_RECEIVED: AwardReceivedEvent,
    EventType.POINTS_MILESTONE: PointsMilestoneEvent,
    EventType.VERSES_STARTED_MILESTONE: VersesStartedMilestoneEvent,
    EventType.VERSE_SET_CREATED: VerseSetCreatedEvent,
    EventType.STARTED_LEARNING_VERSE_SET: StartedLearningVerseSetEvent,
    EventType.AWARD_LOST: AwardLostEvent,
    EventType.GROUP_JOINED: GroupJoinedEvent,
    EventType.GROUP_CREATED: GroupCreatedEvent,
}


for event_type, c in EVENT_CLASSES.items():
    c.event_type = event_type


class EventGroup(object):
    """
    A group of Events all about the same Account.
    """
    def __init__(self, account, events):
        self.account = account
        self.events = events
        self.created = None

    def render_html(self):
        return mark_safe(account_link(self.account) + ":<ul>" +
                         u''.join(["<li>%s</li>" % event.message_html
                                   for event in self.events])
                         + "</ul>")


def dedupe_iterable(iterable, keyfunc):
    seen = set()
    for i in iterable:
        key = keyfunc(i)
        if key in seen:
            continue
        seen.add(key)
        yield i


class EventManager(models.Manager):
    def for_dashboard(self, now=None):
        if now is None:
            now = timezone.now()

        start = now - timedelta(EVENTSTREAM_CUTOFF_DAYS)
        events = list(self.filter(created__gte=start).select_related('account'))
        events = list(dedupe_iterable(events, lambda e:(e.account_id, e.message_html)))
        events.sort(key=lambda e: e.get_rank(), reverse=True)

        # Now group
        grouped_events = []
        for k, g in itertools.groupby(events, lambda e: e.account):
            g = list(g)
            if len(g) == 1:
                grouped_events.append(g[0])
            else:
                if k is None:
                    grouped_events.extend(g)
                else:
                    grouped_events.append(EventGroup(k, g))

        return grouped_events[0:EVENTSTREAM_CUTOFF_NUMBER]


class Event(models.Model):
    message_html = models.TextField()
    event_type = models.PositiveSmallIntegerField(choices=EventType.choice_list)
    weight = models.PositiveSmallIntegerField(default=10)
    event_data = JSONField(blank=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)
    account = models.ForeignKey(Account)

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

    def render_html(self):
        if self.account is not None:
            return mark_safe(account_link(self.account) + u" " + self.message_html)
        else:
            return mark_safe(self.message_html)


import events.hooks
