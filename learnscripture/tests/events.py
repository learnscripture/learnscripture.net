from __future__ import absolute_import

from autofixture import AutoFixture
from django.test import TestCase

from events.models import Event, EventType, NewCommentEvent
from comments.models import Comment
from accounts.models import Account

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
