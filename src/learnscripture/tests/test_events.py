from datetime import timedelta

import django_ftl
from django.utils import timezone
from time_machine import travel

from comments.models import Comment
from events.models import Event, EventType, GroupJoinedEvent, PointsMilestoneEvent

from .base import AccountTestMixin, TestBase
from .test_groups import create_group


class EventTests(AccountTestMixin, TestBase):
    def test_new_comment_event(self):
        _, event_account = self.create_account()
        _, author_account = self.create_account(username="author", email="author@x.com")
        _, author_account2 = self.create_account(username="author2", email="author2@x.com")
        orig_event = PointsMilestoneEvent(account=event_account, points=1000).save()

        # This should create a NewCommentEvent automatically:
        comment = Comment.objects.create(
            author=author_account,
            event=orig_event,
            message="hello",
        )
        event = Event.objects.get(event_type=EventType.NEW_COMMENT)
        assert event.get_absolute_url() == f"/activity/{orig_event.id}/#comment-{comment.id}"

        assert not event.accepts_comments()

        def assert_originator_notification(account, count):
            assert len([n for n in account.identity.notices.all() if "You have new" in n.message_html]) == count

        def assert_contributor_notification(account, count):
            assert len([n for n in account.identity.notices.all() if "There are" in n.message_html]) == count

        # There should also be a notification
        assert_originator_notification(event_account, 1)
        # But not to author
        assert_originator_notification(author_account, 0)
        assert_contributor_notification(author_account, 0)

        # Reply from event_account
        comment = Comment.objects.create(author=event_account, event=orig_event, message="Thanks!")

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
        comment = Comment.objects.create(author=author_account2, event=orig_event, message="another hello")

        assert_originator_notification(event_account, 1)
        assert_contributor_notification(event_account, 0)

        assert_originator_notification(author_account, 0)
        assert_contributor_notification(author_account, 1)

    def test_dashboard_stream(self):
        _, account1 = self.create_account(username="1")
        _, account2 = self.create_account(username="2")
        _, viewer = self.create_account(username="viewer")
        e1 = PointsMilestoneEvent(account=account1, points=100).save()
        e2 = PointsMilestoneEvent(account=account1, points=200).save()
        e3 = PointsMilestoneEvent(account=account2, points=300).save()

        group = create_group()
        group.add_user(account2)
        group.add_user(viewer)
        stream = list(Event.objects.for_dashboard("en", account=viewer))

        # e2 has greater weight than e1, should be earlier
        assert stream.index(e2) < stream.index(e1)

        # account2 and viewer are friends, so e3 should be before e2
        assert stream.index(e3) < stream.index(e2)

    def test_group_comment_event_visibility(self):
        _, account1 = self.create_account(username="1")
        _, viewer = self.create_account(username="viewer")
        group_normal = create_group(quietened=False, public=True)
        group_quiet = create_group(quietened=True, public=True)
        group_private = create_group(public=False)
        group_normal.add_user(account1)
        group_quiet.add_user(account1)
        group_private.add_user(account1)

        group_normal.add_comment(author=account1, message="Hello")
        group_quiet.add_comment(author=account1, message="Hello")
        group_private.add_comment(author=account1, message="Hello")

        comment_events = [
            e for e in Event.objects.for_dashboard("en", account=viewer) if e.event_type == EventType.NEW_COMMENT
        ]
        assert len(comment_events) == 1  # Just the public, non-quiet group
        assert [e.group for e in comment_events] == [group_normal]

    def test_comment_on_group_event(self):
        """
        Test that a comment created on an event that relates to a group
        becomes associated with that group.
        """
        group = create_group()
        _, account1 = self.create_account(username="1")

        event = GroupJoinedEvent(account=account1, group=group).save()
        comment = event.add_comment(author=account1, message="hello")
        assert comment.group == group

    def test_created_display(self):
        with django_ftl.override("en"):
            _, event_account = self.create_account()
            event = PointsMilestoneEvent(account=event_account, points=1000).save()
            assert event.created_display() == "Just now"
            with travel(timezone.now() + timedelta(seconds=5 * 60 + 5)) as tm:
                event.refresh_from_db()
                assert event.created_display() == "5 minutes ago"
                tm.shift(timedelta(seconds=60 * 60))
                event.refresh_from_db()
                assert event.created_display() == "1 hour ago"
                tm.shift(timedelta(seconds=9 * 60 * 60))
                event.refresh_from_db()
                assert event.created_display() == "10 hours ago"
                tm.shift(timedelta(seconds=24 * 60 * 60))
                event.refresh_from_db()
                assert event.created_display() == "1 day ago"
                tm.shift(timedelta(seconds=24 * 60 * 60))
                event.refresh_from_db()
                assert event.created_display() == "2 days ago"
