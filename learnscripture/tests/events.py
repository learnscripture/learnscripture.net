from __future__ import absolute_import

from autofixture import AutoFixture
from django.test import TestCase

from events.models import Event, EventType, NewCommentEvent
from comments.models import Comment
from accounts.models import Account

class EventTests(TestCase):

    def test_new_comment_event_url(self):
        account = AutoFixture(Account).create(1)[0]
        orig_event = (AutoFixture(Event,
                                  field_values={'event_data': {}})
                      .create(1)[0])
        comment = Comment.objects.create(
            author=account,
            event=orig_event,
            message="hello",
            )
        event = NewCommentEvent(
            account=account,
            comment=comment,
            parent_event=orig_event
            ).save()
        self.assertEqual(event.get_absolute_url(),
                         '/activity/%s/#comment-%s' % (orig_event.id,
                                                       comment.id))

