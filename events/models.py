from datetime import timedelta
import itertools
import math

from django.db import models
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from jsonfield import JSONField

from accounts.models import Account
from awards.utils import award_link
from groups.models import Group
from groups.utils import group_link
from learnscripture.datastructures import make_class_enum
from learnscripture.templatetags.account_utils import account_link


EVENTSTREAM_CUTOFF_DAYS = 3 # just 3 days of events
EVENTSTREAM_CUTOFF_NUMBER = 8

# Arbitrarily say stuff is 50% less interesting when it is half a day old.
HALF_LIFE_DAYS = 0.5
EVENTSTREAM_TIME_DECAY_FACTOR = 3600*24*HALF_LIFE_DAYS

# Events have an affinity of 1.0 normally, and this can be boosted by the amount
# below for a maximum friendship level
EVENTSTREAM_MAX_EXTRA_AFFINITY_FOR_FRIEND = 1.0

# With EVENTSTREAM_CUTOFF_DAYS = 3, and HALF_LIFE_DAYS=0.5 there is a factor of
# 64 (6 half lives) to play with: if an event has a weight more than 64 times
# higher than the rest of the stream, it will stay at the top of the event
# stream until it disappears altogether. But we want to be phasing things out
# more quickly, so we avoid such extreme factors.


class EventLogic(object):
    """
    Encapsulates logic about different types of events.

    This is used instead of having Event subclasses, which usually leads to
    performance problems. Event stores data, and all polymorphism behaviour is
    defined in EventLogic.
    """
    weight = 10

    @property
    def event_type(self):
        return self.enum_val

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
        return self.event

    # EventLogic instances are only created when the Event is first created. In
    # some cases Event wants to delegate some decisions to EventLogic and
    # subclasses, without creating an EventLogic instance. We use the following
    # classmethods:

    @classmethod
    def get_absolute_url(cls, event):
        return reverse('activity_item', args=(event.id,))

    @classmethod
    def accepts_comments(cls, event):
        return True

    @classmethod
    def get_group(cls, event):
        return None


class GeneralEvent(EventLogic):
    # No longer used.
    pass


class NewAccountEvent(EventLogic):

    def __init__(self, account=None):
        super(NewAccountEvent, self).__init__(account=account)
        self.event.message_html = u"signed up to LearnScripture.net"


class AwardReceivedEvent(EventLogic):

    # Awards are quite interesting
    weight = 12

    def __init__(self, award=None):
        super(AwardReceivedEvent, self).__init__(award_id=award.id,
                                                 account=award.account)
        self.event.message_html = u"earned " + award_link(award)


class AwardLostEvent(EventLogic):

    weight = AwardReceivedEvent.weight

    def __init__(self, award=None):
        super(AwardLostEvent, self).__init__(award_id=award.id,
                                             account=award.account)
        self.event.message_html = u"lost " + award_link(award)


class VerseSetCreatedEvent(EventLogic):

    def __init__(self, verse_set=None):
        super(VerseSetCreatedEvent, self).__init__(verse_set_id=verse_set.id,
                                                   account=verse_set.created_by)
        self.event.message_html = format_html(
            u'created new verse set <a href="{0}">{1}</a>',
            reverse('view_verse_set', args=(verse_set.slug,)),
            verse_set.name
            )


class StartedLearningVerseSetEvent(EventLogic):

    weight = 13

    def __init__(self, verse_set=None, chosen_by=None):
        super(StartedLearningVerseSetEvent, self).__init__(verse_set_id=verse_set.id,
                                                           account=chosen_by)
        self.event.message_html = format_html(
            'started learning <a href="{0}">{1}</a>',
            reverse('view_verse_set', args=(verse_set.slug,)),
            verse_set.name
            )


class PointsMilestoneEvent(EventLogic):
    def __init__(self, account=None, points=None):
        super(PointsMilestoneEvent, self).__init__(account=account,
                                                   points=points)
        self.event.message_html = format_html(
            u'reached {0} points', intcomma(points)
            )


class VersesStartedMilestoneEvent(EventLogic):
    def __init__(self, account=None, verses_started=None):
        super(VersesStartedMilestoneEvent, self).__init__(account=account,
                                                          verses_started=verses_started)
        self.event.message_html = format_html(
            u'reached {0} verses started', intcomma(verses_started)
            )


class GroupRelatedMixin(object):
    # Subclasses must store 'group_id' in event.event_data
    @classmethod
    def get_group(cls, event):
        return Group.objects.get(id=event.event_data['group_id'])


class GroupJoinedEvent(GroupRelatedMixin, EventLogic):

    weight = 11

    def __init__(self, account=None, group=None):
        super(GroupJoinedEvent, self).__init__(account=account,
                                               group_id=group.id)

        self.event.message_html = format_html(
            u"joined group {0}", group_link(group)
            )


class GroupCreatedEvent(GroupRelatedMixin, EventLogic):

    def __init__(self, account=None, group=None):
        super(GroupCreatedEvent, self).__init__(account=account,
                                                group_id=group.id)
        self.event.message_html = format_html(
            u"created group {0}", group_link(group)
            )


class VersesFinishedMilestoneEvent(EventLogic):
    def __init__(self, account, verses_finished=None):
        super(VersesFinishedMilestoneEvent, self).__init__(account=account,
                                                           verses_finished=verses_finished)
        self.event.message_html = format_html(
            u"reached {0} verses finished", intcomma(verses_finished)
            )


class StartedLearningCatechismEvent(EventLogic):

    def __init__(self, account=None, catechism=None):
        super(StartedLearningCatechismEvent, self).__init__(account=account,
                                                            catechism_id=catechism.id)
        self.event.message_html = format_html(
            u'started learning <a href="{0}">{1}</a>',
            reverse('view_catechism', args=(catechism.slug,)),
            catechism.full_name,
            )


class NewCommentEvent(EventLogic):

    weight = 11

    def __init__(self, account=None, comment=None, parent_event=None):
        super(NewCommentEvent, self).__init__(account=account,
                                              comment_id=comment.id)
        self.event.message_html = format_html(
            u'posted a <a href="{0}">comment</a> on {1}',
            comment.get_absolute_url(),
            comment.get_subject_html(),
            )
        self.event.parent_event = comment.event

    @classmethod
    def get_absolute_url(cls, event):
        # NewCommentEvent cannot collect comments themselves.
        # So URL for new comment event is the comment's URL.
        from comments.models import Comment
        return Comment.objects.get(id=event.event_data['comment_id']).get_absolute_url()

    @classmethod
    def accepts_comments(cls, event):
        return False


EventType = make_class_enum(
    'EventType',
    [(1, 'GENERAL', 'General', GeneralEvent), # No longer used
     (2, 'NEW_ACCOUNT', 'New account', NewAccountEvent),
     (3, 'AWARD_RECEIVED', 'Award received', AwardReceivedEvent),
     (4, 'POINTS_MILESTONE', 'Points milestone', PointsMilestoneEvent),
     (5, 'VERSES_STARTED_MILESTONE', 'Verses started milestone', VersesStartedMilestoneEvent),
     (6, 'VERSES_FINISHED_MILESTONE', 'Verses finished milestone', VersesFinishedMilestoneEvent),
     (7, 'VERSE_SET_CREATED', 'Verse set created', VerseSetCreatedEvent),
     (8, 'STARTED_LEARNING_VERSE_SET', 'Started learning a verse set', StartedLearningVerseSetEvent),
     (9, 'AWARD_LOST', 'Award lost', AwardLostEvent),
     (10, 'GROUP_JOINED', 'Group joined', GroupJoinedEvent),
     (11, 'GROUP_CREATED', 'Group created', GroupCreatedEvent),
     (12, 'STARTED_LEARNING_CATECHISM', 'Started learning catechism', StartedLearningCatechismEvent),
     (13, 'NEW_COMMENT', 'New comment', NewCommentEvent),
     ])


def dedupe_iterable(iterable, keyfunc):
    """
    Removes duplicates from an iterable, while preserving order.
    """
    seen = set()
    for i in iterable:
        key = keyfunc(i)
        if key in seen:
            continue
        seen.add(key)
        yield i


class EventManager(models.Manager):
    def for_dashboard(self, now=None, account=None):
        if now is None:
            now = timezone.now()

        start = now - timedelta(EVENTSTREAM_CUTOFF_DAYS)
        events = (self
                  .filter(created__gte=start)
                  .prefetch_related('account')
                  .exclude(event_type=EventType.NEW_COMMENT,
                           account=account)
                  .annotate(comment_count=models.Count('comments'))
                  )
        if account is None or not account.is_hellbanned:
            events = events.exclude(account__is_hellbanned=True)
        events = list(events)
        events = list(dedupe_iterable(events, lambda e:(e.account_id, e.message_html)))

        if account is not None:
            friendship_weights = account.get_friendship_weights()
        else:
            friendship_weights = None

        events.sort(key=lambda e: e.get_rank(viewer=account,
                                             friendship_weights=friendship_weights,
                                             now=now),
                    reverse=True)

        return events[:EVENTSTREAM_CUTOFF_NUMBER]

    def for_activity_stream(self, viewer=None, event_by=None):
        qs = (Event.objects
              .order_by('-created')
              .select_related('account')
              )
        if event_by is None:
            qs = qs.exclude(event_type=EventType.NEW_COMMENT)
        if viewer is None or not viewer.is_hellbanned:
            qs = qs.exclude(account__is_hellbanned=True)
        if event_by is not None:
            qs = qs.filter(account=event_by)

        return qs


class Event(models.Model):
    message_html = models.TextField()
    event_type = models.PositiveSmallIntegerField(choices=EventType.choice_list)
    weight = models.PositiveSmallIntegerField(default=10)
    event_data = JSONField(blank=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)
    account = models.ForeignKey(Account)

    # Events like NewCommentEvent have a parent event (the event the comment is
    # attached to).
    parent_event = models.ForeignKey('self', null=True, blank=True)

    objects = EventManager()

    def __repr__(self):
        return "<Event id=%s type=%s>" % (self.id, self.event_type)

    def __unicode__(self):
        return u"Event %d" % self.id

    def get_rank(self, viewer=None, friendship_weights=None, now=None):
        """
        Returns the overall weighting for this event, given the viewing account.
        """
        # Don't ever want to see 'new comment' events from myself.
        if (viewer is not None and
            self.event_type == EventType.NEW_COMMENT and
            self.account_id == viewer.id):
            return 0

        if viewer is not None and friendship_weights is None:
            friendship_weights = viewer.get_friendship_weights()

        affinity = 1.0
        if friendship_weights is not None:
            affinity += friendship_weights.get(self.account_id, 0) * EVENTSTREAM_MAX_EXTRA_AFFINITY_FOR_FRIEND

        if now is None:
            now = timezone.now()

        seconds = (now - self.created).total_seconds()

        recency = 2 ** (-seconds/EVENTSTREAM_TIME_DECAY_FACTOR)
        return self.weight * recency * affinity

    def created_display(self):
        from django.utils.timesince import timesince
        now = timezone.now()
        diff = now - self.created
        if diff.total_seconds() < 60:
            return u"Just now"
        return timesince(self.created, now=now) + u" ago"

    def render_html(self):
        if self.account is not None:
            return format_html("{0} {1}", account_link(self.account),
                               mark_safe(self.message_html))
        else:
            return mark_safe(self.message_html)

    @cached_property
    def event_logic(self):
        """
        Returns the EventLogic subclass for this event.
        """
        return EventType.classes[self.event_type]

    def get_absolute_url(self):
        return self.event_logic.get_absolute_url(self)

    def accepts_comments(self):
        return self.event_logic.accepts_comments(self)

    def add_comment(self, author=None, message=None):
        assert self.accepts_comments()
        return self.comments.create(author=author,
                                    message=message,
                                    group=self.get_group())

    def get_group(self):
        return self.event_logic.get_group(self)


import events.hooks
