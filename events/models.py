import math
from datetime import timedelta

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from jsonfield import JSONField

from accounts.models import Account
from bibleverses.models import verse_set_smart_name
from common.utils.html import link
from groups.models import Group
from learnscripture.datastructures import lazy_dict_like, make_class_enum
from learnscripture.ftl_bundles import t
from learnscripture.templatetags.account_utils import account_link

EVENTSTREAM_CUTOFF_DAYS = 3  # just 3 days of events
EVENTSTREAM_CUTOFF_NUMBER = 8

# Arbitrarily say stuff is 50% less interesting when it is half a day old.
HALF_LIFE_DAYS = 0.5
EVENTSTREAM_TIME_DECAY_FACTOR = 3600 * 24 * HALF_LIFE_DAYS

# Events have an affinity of 1.0 normally, and this can be boosted by the amount
# below for a maximum friendship level
EVENTSTREAM_MAX_EXTRA_AFFINITY_FOR_FRIEND = 2.0

# With EVENTSTREAM_CUTOFF_DAYS = 3, and HALF_LIFE_DAYS=0.5 there is a factor of
# 64 (6 half lives) to play with: if an event has a weight more than 64 times
# higher than the rest of the stream, it will stay at the top of the event
# stream until it disappears altogether. But we want to be phasing things out
# more quickly, so we avoid such extreme factors.


class EventLogic(object):
    """
    Encapsulates logic about different types of events.

    Event stores data, and all polymorphic behaviour is defined in EventLogic.

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
         - anything else - stored in Event.event_data,
           so must be simple types that can be serialised to JSON.

        The EventLogic subclasses `__init__` methods should
        pass everything needed by their get_message_html()
        method into Event.event_data, via a super().__init__() calls.
        """
        account = kwargs.pop('account', None)
        self.event_data = kwargs
        self.event = Event(weight=self.weight,
                           event_type=self.event_type,
                           account=account)

    def save(self):
        self.event.event_data = self.event_data
        self.event.save()
        # Force population of Event.url, to avoid doing it later.
        self.event.get_absolute_url()
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


class NewAccountEvent(EventLogic):
    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-new-user-signed-up-html',
                 dict(username=account_link(event.account)))


class AwardReceivedEvent(EventLogic):

    # Awards are quite interesting
    weight = 12

    def __init__(self, award=None):
        from awards.models import AwardType
        super(AwardReceivedEvent, self).__init__(award_id=award.id,
                                                 award_type=award.award_type,
                                                 award_level=award.level,
                                                 temporary_award=award.award_type in [AwardType.REIGNING_WEEKLY_CHAMPION],
                                                 account=award.account)

    @classmethod
    def get_message_html(cls, event, language_code):
        from awards.models import AwardType
        award_type = event.event_data['award_type']
        award_level = event.event_data['award_level']
        award_class = AwardType.classes[award_type]
        award_detail = award_class(level=award_level)
        return t('evemts-award-received-html',
                 dict(username=account_link(event.account),
                      award=link(reverse('award', args=(award_class.slug(),)),
                                 award_detail.short_description())))


class AwardLostEvent(EventLogic):

    weight = AwardReceivedEvent.weight

    def __init__(self, award=None):
        super(AwardLostEvent, self).__init__(award_id=award.id,
                                             award_type=award.award_type,
                                             account=award.account)

    @classmethod
    def get_message_html(cls, event, language_code):
        from awards.models import AwardType
        award_type = event.event_data['award_type']
        award_level = event.event_data['award_level']
        award_class = AwardType.classes[award_type]
        award_detail = award_class(level=award_level)
        return t('events-award-lost-html',
                 dict(username=account_link(event.account),
                      award=link(reverse('award', args=(award_class.slug(),)),
                                 award_detail.short_description())))


class VerseSetCreatedEvent(EventLogic):

    def __init__(self, verse_set=None):
        super(VerseSetCreatedEvent, self).__init__(verse_set_id=verse_set.id,
                                                   verse_set_slug=verse_set.slug,
                                                   verse_set_name=verse_set.name,
                                                   verse_set_language_code=verse_set.language_code,
                                                   account=verse_set.created_by)

    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-verse-set-created-html',
                 dict(username=account_link(event.account),
                      verseset=link(
                          reverse('view_verse_set', args=(event.event_data['verse_set_slug'],)),
                          verse_set_smart_name(
                              event.event_data['verse_set_name'],
                              event.event_data['verse_set_language_code'],
                              language_code))))


class StartedLearningVerseSetEvent(EventLogic):

    weight = 13

    def __init__(self, verse_set=None, chosen_by=None):
        super(StartedLearningVerseSetEvent, self).__init__(verse_set_id=verse_set.id,
                                                           verse_set_slug=verse_set.slug,
                                                           verse_set_name=verse_set.name,
                                                           verse_set_language_code=verse_set.language_code,
                                                           account=chosen_by)

    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-started-learning-verse-set-html',
                 dict(username=account_link(event.account),
                      verseset=link(reverse('view_verse_set', args=(event.event_data['verse_set_slug'],)),
                                    verse_set_smart_name(
                                        event.event_data['verse_set_name'],
                                        event.event_data['verse_set_language_code'],
                                        language_code))))


class PointsMilestoneEvent(EventLogic):
    def __init__(self, account=None, points=None):
        super(PointsMilestoneEvent, self).__init__(account=account,
                                                   points=points)

    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-points-milestone-reached-html',
                 dict(username=account_link(event.account),
                      points=event.event_data['points']))


class VersesStartedMilestoneEvent(EventLogic):
    def __init__(self, account=None, verses_started=None):
        super(VersesStartedMilestoneEvent, self).__init__(account=account,
                                                          verses_started=verses_started)

    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-verses-started-milestone-reached-html',
                 dict(username=account_link(event.account),
                      verses=event.event_data['verses_started']))


class GroupJoinedEvent(EventLogic):

    weight = 11

    def __init__(self, account=None, group=None):
        super(GroupJoinedEvent, self).__init__(account=account,
                                               group_name=group.name,
                                               group_slug=group.slug,
                                               group_id=group.id)
        self.event.group = group

    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-user-joined-group-html',
                 dict(username=account_link(event.account),
                      group=link(reverse('group', args=(event.event_data['group_slug'],)),
                                 event.event_data['group_name'])))


class GroupCreatedEvent(EventLogic):

    def __init__(self, account=None, group=None):
        super(GroupCreatedEvent, self).__init__(account=account,
                                                group_name=group.name,
                                                group_slug=group.slug,
                                                group_id=group.id)
        self.event.group = group

    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-user-created-group-html',
                 dict(username=account_link(event.account),
                      group=link(reverse('group', args=(event.event_data['group_slug'],)),
                                 event.event_data['group_name'])))


class VersesFinishedMilestoneEvent(EventLogic):
    def __init__(self, account, verses_finished=None):
        super(VersesFinishedMilestoneEvent, self).__init__(account=account,
                                                           verses_finished=verses_finished)

    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-verses-finished-milestone-reached-html',
                 dict(username=account_link(event.account),
                      verses=event.event_data['verses_finished']))


class StartedLearningCatechismEvent(EventLogic):

    def __init__(self, account=None, catechism=None):
        super(StartedLearningCatechismEvent, self).__init__(account=account,
                                                            catechism_slug=catechism.slug,
                                                            catechism_name=catechism.full_name,
                                                            catechism_id=catechism.id)

    @classmethod
    def get_message_html(cls, event, language_code):
        return t('events-started-learning-catechism-html',
                 dict(username=account_link(event.account),
                      catechism=link(
                          reverse('view_catechism', args=(event.event_data['catechism_slug'],)),
                          event.event_data['catechism_name'])))


class NewCommentEvent(EventLogic):

    weight = 11

    # weight for comments on group walls where the user is a member
    group_wall_weight = 20

    def __init__(self, account=None, comment=None, parent_event=None):
        kwargs = dict(account=account,
                      comment_id=comment.id)
        if comment.group_id is not None:
            kwargs['group_id'] = comment.group_id
            kwargs['group_slug'] = comment.group.slug
            kwargs['group_name'] = comment.group.name
        if comment.event_id is not None:
            kwargs['parent_event_id'] = comment.event.id
            kwargs['parent_event_account_id'] = comment.event.account.id
            kwargs['parent_event_account_username'] = comment.event.account.username
        super(NewCommentEvent, self).__init__(**kwargs)
        self.event.parent_event = comment.event
        self.event.group = comment.group

    @classmethod
    def get_absolute_url(cls, event):
        # NewCommentEvent cannot collect comments themselves.
        # So URL for new comment event is the comment's URL.
        from comments.models import Comment
        return Comment.objects.get(id=event.event_data['comment_id']).get_absolute_url()

    @classmethod
    def accepts_comments(cls, event):
        return False

    @classmethod
    def get_message_html(cls, event, language_code):
        comment_id = event.event_data['comment_id']
        if 'parent_event_id' in event.event_data:
            return t('events-comment-on-activity-html',
                     dict(username=account_link(event.account),
                          comment_url=get_absolute_url_for_event_comment(event, comment_id),
                          other_user=link(reverse('user_stats', args=(event.event_data['parent_event_account_username'],)),
                                          event.event_data['parent_event_account_username'])))

        elif 'group_id' in event.event_data:
            group_slug = event.event_data['group_slug']
            return t('events-comment-on-group-wall-html',
                     dict(username=account_link(event.account),
                          comment_url=get_absolute_url_for_group_comment(event, comment_id, group_slug),
                          group=link(reverse('group', args=(group_slug,)),
                                     event.event_data['group_name'])))

        else:
            raise AssertionError("Expected one of parent_event_id or group_id for event {0}"
                                 .format(event.id))


EventType = make_class_enum(
    'EventType',
    [('NEW_ACCOUNT', 'New account', NewAccountEvent),
     ('AWARD_RECEIVED', 'Award received', AwardReceivedEvent),
     ('POINTS_MILESTONE', 'Points milestone', PointsMilestoneEvent),
     ('VERSES_STARTED_MILESTONE', 'Verses started milestone', VersesStartedMilestoneEvent),
     ('VERSES_FINISHED_MILESTONE', 'Verses finished milestone', VersesFinishedMilestoneEvent),
     ('VERSE_SET_CREATED', 'Verse set created', VerseSetCreatedEvent),
     ('STARTED_LEARNING_VERSE_SET', 'Started learning a verse set', StartedLearningVerseSetEvent),
     ('AWARD_LOST', 'Award lost', AwardLostEvent),
     ('GROUP_JOINED', 'Group joined', GroupJoinedEvent),
     ('GROUP_CREATED', 'Group created', GroupCreatedEvent),
     ('STARTED_LEARNING_CATECHISM', 'Started learning catechism', StartedLearningCatechismEvent),
     ('NEW_COMMENT', 'New comment', NewCommentEvent),
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
    def for_dashboard(self, language_code, now=None, account=None):
        if now is None:
            now = timezone.now()

        start = now - timedelta(EVENTSTREAM_CUTOFF_DAYS)
        events = (self
                  .for_viewer(account)
                  .filter(created__gte=start)
                  .select_related('account')
                  .exclude(event_type=EventType.NEW_COMMENT,
                           account=account)
                  .annotate(comment_count=models.Count('comments'))
                  )
        if account is None or not account.is_hellbanned:
            events = events.exclude(account__is_hellbanned=True)
        events = list(events)
        # Avoid repeated messages. Events with the same event type, account id
        # and data will produce the same message.
        events = list(dedupe_iterable(events,
                                      lambda e: (e.account_id,
                                                 e.event_type,
                                                 tuple(sorted(e.event_data.items())))))

        if account is not None:
            friendship_weights = account.get_friendship_weights()
            group_ids = list(account.groups.values_list('id', flat=True))
        else:
            friendship_weights = None
            group_ids = []

        events.sort(key=lambda e: e.get_rank(viewer=account,
                                             friendship_weights=friendship_weights,
                                             group_ids=group_ids,
                                             now=now),
                    reverse=True)

        # Limit
        events = events[:EVENTSTREAM_CUTOFF_NUMBER]
        # Now sort by time
        events.sort(key=lambda e: e.created, reverse=True)
        return events

    def for_viewer(self, viewer):
        qs_base = (Event.objects
                   .order_by('-created')
                   .select_related('account')
                   .exclude(account__is_active=False)
                   )
        if viewer is None or not viewer.is_hellbanned:
            qs_base = qs_base.exclude(account__is_hellbanned=True)

        # Exclude all comments from private groups
        qs_1 = qs_base.exclude(group__isnull=False,
                               group__public=False)

        if viewer is not None:
            # Re-add events from groups
            qs_2 = qs_base.filter(group__isnull=False,
                                  group__in=viewer.groups.all())
            qs = qs_1 | qs_2
        else:
            qs = qs_1

        return qs

    def for_activity_stream(self, viewer=None, event_by=None):
        qs = self.for_viewer(viewer)
        if event_by is None:
            # On the main activity stream, comments on parent events are
            # included on that parent event, so don't show them separately as
            # well.
            qs = qs.exclude(event_type=EventType.NEW_COMMENT,
                            parent_event__isnull=False)
        if event_by is not None:
            qs = qs.filter(account=event_by)
        return qs


class Event(models.Model):
    event_type = models.CharField(max_length=40, choices=EventType.choice_list)
    weight = models.PositiveSmallIntegerField(default=10)
    event_data = JSONField(blank=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    # If the event relates to something in a Group, this should be set
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.CASCADE)

    # Events like NewCommentEvent have a parent event (the event the comment is
    # attached to).
    parent_event = models.ForeignKey('self', on_delete=models.CASCADE,
                                     null=True, blank=True)

    # Denormalized value
    url = models.CharField(max_length=255, blank=True)

    objects = EventManager()

    def __repr__(self):
        return "<Event id=%s type=%s>" % (self.id, self.event_type)

    def __str__(self):
        return "Event %d" % self.id

    def get_rank(self, viewer=None, friendship_weights=None,
                 group_ids=None, now=None):
        """
        Returns the overall weighting for this event, given the viewing account.
        """
        # Don't ever want to see 'new comment' events from myself.
        if (viewer is not None and
            self.event_type == EventType.NEW_COMMENT and
                self.account_id == viewer.id):
            return 0

        if group_ids is None:
            group_ids = []

        # Weight
        weight = self.weight

        if self.event_type == EventType.NEW_COMMENT:
            if self.group_id in group_ids:
                # This is a comment on a group wall that the user is in.
                weight = self.event_logic.group_wall_weight

        # Affinity
        if viewer is not None and friendship_weights is None:
            friendship_weights = viewer.get_friendship_weights()

        affinity = 1.0
        if friendship_weights is not None:
            affinity += friendship_weights.get(self.account_id, 0) * EVENTSTREAM_MAX_EXTRA_AFFINITY_FOR_FRIEND

        # Recency
        if now is None:
            now = timezone.now()

        seconds = (now - self.created).total_seconds()

        recency = 2 ** (-seconds / EVENTSTREAM_TIME_DECAY_FACTOR)

        return weight * recency * affinity

    def created_display(self):
        now = timezone.now()
        diff = now - self.created
        seconds = float(diff.total_seconds())
        if seconds < 60:
            return t('events-time-since-just-now')
        minutes = math.floor(seconds / 60)
        if minutes < 60:
            return t('events-time-since-minutes', dict(minutes=minutes))
        hours = math.floor(minutes / 60)
        if hours < 24:
            return t('events-time-since-hours', dict(hours=hours))
        days = math.floor(hours / 24)
        return t('events-time-since-days', dict(days=days))

    def render_html(self, language_code):
        return self.event_logic.get_message_html(self, language_code)

    @lazy_dict_like
    def render_html_dict(self, language_code):
        return self.render_html(language_code)

    @cached_property
    def event_logic(self):
        """
        Returns the EventLogic subclass for this event.
        """
        return EventType.classes[self.event_type]

    def get_absolute_url(self):
        if not self.url:
            url = self.event_logic.get_absolute_url(self)
            self.url = url
            if self.id is not None:
                Event.objects.filter(id=self.id).update(url=url)
        return self.url

    def accepts_comments(self):
        return self.event_logic.accepts_comments(self)

    def add_comment(self, author=None, message=None):
        assert self.accepts_comments()
        return self.comments.create(author=author,
                                    message=message,
                                    group=self.group)

    @property
    def is_new_comment(self):
        return self.event_type == EventType.NEW_COMMENT

    def get_comment(self):
        from comments.models import Comment
        try:
            return Comment.objects.get(id=int(self.event_data['comment_id']))
        except (KeyError, Comment.DoesNotExist):
            return None

    def ordered_comments(self):
        if hasattr(self, '_prefetched_objects_cache'):
            if 'comments' in self._prefetched_objects_cache:
                return sorted(self._prefetched_objects_cache['comments'],
                              key=lambda c: c.created)
        return self.comments.all().order_by('created').select_related('author')


def get_absolute_url_for_event_comment(event, comment_id):
    return event.get_absolute_url() + "#comment-%s" % comment_id


def get_absolute_url_for_group_comment(event, comment_id, group_slug):
    return reverse('group_wall', args=(group_slug,)) + "?comment=%s" % comment_id
