from __future__ import absolute_import

from autofixture import AutoFixture
from django.test import TestCase
from django.utils import timezone

from events.models import Event, EventType, GroupJoinedEvent, PointsMilestoneEvent
from comments.models import Comment
from groups.models import Group

from .base import AccountTestMixin

__all__ = ['EventTests']


class EventTests(AccountTestMixin, TestCase):

    def test_new_comment_event(self):
        _, event_account = self.create_account()
        _, author_account = self.create_account(username="author",
                                                email="author@x.com")
        _, author_account2 = self.create_account(username="author2",
                                                 email="author2@x.com")
        orig_event = PointsMilestoneEvent(account=event_account, points=1000).save()

        # This should create a NewCommentEvent automatically:
        comment = Comment.objects.create(
            author=author_account,
            event=orig_event,
            message="hello",
            )
        event = Event.objects.get(event_type=EventType.NEW_COMMENT)
        self.assertEqual(event.get_absolute_url(),
                         '/activity/%s/#comment-%s' % (orig_event.id,
                                                       comment.id))

        self.assertFalse(event.accepts_comments())

        def assert_originator_notification(account, count):
            self.assertEqual(len([n for n in account.identity.notices.all()
                              if "You have new" in n.message_html]),
                             count)
        def assert_contributor_notification(account, count):
            self.assertEqual(len([n for n in account.identity.notices.all()
                              if "There are" in n.message_html]),
                             count)

        # There should also be a notification
        assert_originator_notification(event_account, 1)
        # But not to author
        assert_originator_notification(author_account, 0)
        assert_contributor_notification(author_account, 0)

        # Reply from event_account
        comment = Comment.objects.create(
            author=event_account,
            event=orig_event,
            message="Thanks!"
            )


        # We should not have duplicated notifications for event_account
        assert_originator_notification(event_account, 1)
        assert_contributor_notification(event_account, 0)

        assert_originator_notification(author_account, 0)
        assert_contributor_notification(author_account, 1)

        # Clear
        event_account.identity.notices.all().delete()
        author_account.identity.notices.all().delete()

        # Comment from someone else should generate a notification
        # to all contributors
        comment = Comment.objects.create(
            author=author_account2,
            event=orig_event,
            message="another hello"
            )

        assert_originator_notification(event_account, 1)
        assert_contributor_notification(event_account, 0)

        assert_originator_notification(author_account, 0)
        assert_contributor_notification(author_account, 1)


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

    def test_comment_on_group_event(self):
        """
        Test that a comment created on an event that relates to a group
        becomes associated with that group.
        """
        group = AutoFixture(Group, generate_fk=True).create(1)[0]
        _, account1 = self.create_account(username="1")

        event = GroupJoinedEvent(account=account1, group=group).save()
        comment = event.add_comment(author=account1,
                                    message="hello")
        self.assertEqual(comment.group, group)
