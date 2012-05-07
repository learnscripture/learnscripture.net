from django.db import models
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.html import escape
from jsonfield import JSONField

from learnscripture.datastructures import make_choices

EventType = make_choices('EventType',
                         [(1, 'NOTICE', 'Notice'),
                          (2, 'NEW_ACCOUNT', 'New account'),
                          (3, 'AWARD_RECEIVED', 'Award received'),
                          (4, 'POINTS_MILESTONE', 'Points milestone'),
                          (5, 'VERSES_STARTED_MILESTONE', 'Verses started milestone'),
                          (6, 'VERSES_FINISHED_MILESTONE', 'Verses finished milestone'),
                          (7, 'VERSE_SET_CREATED', 'Verse set created'),
                          (8, 'VERSE_SET_STARTED', 'Verse set started'),
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
    weight = 1000


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
                                             [reverse('user_stats', args=(account.username,)),
                                              account.username,
                                              extra_name]))
                                   )


EVENT_CLASSES = {
    EventType.NEW_ACCOUNT: NewAccountEvent
}

for event_type, c in EVENT_CLASSES.items():
    c.event_type = event_type


class Event(models.Model):
    message_html = models.TextField()
    event_type = models.PositiveSmallIntegerField(choices=EventType.choice_list)
    weight = models.PositiveSmallIntegerField(default=10)
    event_data = JSONField(blank=True)
    created = models.DateTimeField(default=timezone.now, db_index=True)

    def __unicode__(self):
        return "Event %d" % self.id
