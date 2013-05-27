from __future__ import absolute_import

from autofixture import AutoFixture
from django.test import TestCase
from django.utils import timezone

from events.models import Event, EventType, NewCommentEvent
from comments.models import Comment
from accounts.models import Account
from groups.models import Group

from .base import AccountTestMixin

class EventTests(AccountTestMixin, TestCase):

    def test_new_comment_event(self):
        _, event_account = self.create_account()
        _, author_account = self.create_account(username="author",
                                                email="author@x.com")
        orig_event = (AutoFixture(Event,
                                  field_values={'event_data': {},
                                                'account': event_account,
                                                })
                      .create(1)[0])
        # This should create a NewCommentEvent automatically
        comment = Comment.objects.create(
            author=author_account,
            event=orig_event,
            message="hello",
            )
        event = Event.objects.get(event_type=EventType.NEW_COMMENT)
        self.assertEqual(event.get_absolute_url(),
                         '/activity/%s/#comment-%s' % (orig_event.id,
                                                       comment.id))

        # There should also be a notification
        self.assertEqual(len([n for n in event_account.identity.notices.all()
                              if "You have new" in n.message_html]),
                         1)

    def test_dashboard_stream(self):
        _, account1 = self.create_account(username="1")
        _, account2 = self.create_account(username="2")
        _, viewer = self.create_account(username="viewer")
        now = timezone.now()
        e1 = Event.objects.create(
            message_html="Event 1",
            event_data={},
            event_type=0,
            created=now,
            weight=10,
            account=account1,
            )
        e2 = Event.objects.create(
            message_html="Event 2",
            event_data={},
            event_type=0,
            created=now,
            weight=11,
            account=account1,
            )
        e3 = Event.objects.create(
            message_html="Event 3",
            event_data={},
            event_type=0,
            created=now,
            weight=11,
            account=account2,
            )

        group = AutoFixture(Group).create(1)[0]
        group.add_user(account2)
        group.add_user(viewer)
        stream = list(Event.objects.for_dashboard(account=viewer))

        # e2 has greater weight than e1, should be earlier
        self.assertTrue(stream.index(e2) < stream.index(e1))

        # account2 and viewer are friends, so e3 should be before e2
        self.assertTrue(stream.index(e3) < stream.index(e2))
