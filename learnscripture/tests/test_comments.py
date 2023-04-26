import time

from accounts.models import Account, Identity
from comments.models import Comment, hide_comment
from events.models import Event, EventType, PointsMilestoneEvent
from groups.models import Group
from moderation import models as moderation

from .base import AccountTestMixin, Auto, FullBrowserTest, TestBase, create_account
from .test_groups import create_group


def create_commentable_event() -> tuple[Event, Identity]:
    event_identity, event_account = create_account(username="eventaccount", email="eventaccount@a.com")
    event = PointsMilestoneEvent(account=event_account, points=1000).save()
    event_identity.notices.all().delete()
    return event, event_identity


def create_comment(
    *, author: Account, event: Event = Auto, group: Group = Auto, message="This is a comment", hidden=False
) -> Comment:
    if event:
        create = event.comments.create
    elif group:
        create = group.comments.create
    else:
        raise AssertionError("Must pass event or group")
    return create(author=author, message=message, hidden=hidden)


class CommentPageTests(FullBrowserTest):
    def test_add_comment(self):
        event, event_identity = create_commentable_event()
        _, account = create_account()
        self.login(account)
        self.get_url("activity_stream")
        self.click(".show-add-comment")
        self.fill({".commentblock .comment-box": (message := "This is my comment")})
        self.click(".commentblock .add-comment-btn")
        self.wait_for_ajax()

        # Test page
        self.assertTextPresent(message)

        # Test db
        c = Comment.objects.get()
        assert c.author == account
        assert c.message == message

        # Test event created
        assert Event.objects.filter(parent_event=event, event_type=EventType.NEW_COMMENT, account=account).count() == 1

        # Test notice created
        assert event_identity.notices.filter(related_event=event).count() == 1

    def test_no_event_from_hellbanned_users(self):
        event, _ = create_commentable_event()
        _, account = create_account(is_hellbanned=True)
        self.login(account)
        self.get_url("activity_stream")
        self.click(".show-add-comment")
        self.fill({".commentblock .comment-box": (message := "This is my comment")})
        self.click(".commentblock .add-comment-btn")
        time.sleep(1)

        # Test db - user should be able to see own message
        c = Comment.objects.visible_for_account(account).get()
        assert c.author == account
        assert c.message == message

        # Test event NOT created
        assert Event.objects.filter(parent_event=event, event_type=EventType.NEW_COMMENT, account=account).count() == 0

    def test_moderate_comment(self):
        event, _ = create_commentable_event()
        _, account = create_account(is_moderator=True)
        _, other_account = self.create_account(username="other", email="other@other.com")

        c1 = create_comment(author=other_account, event=event, message="This is a naughty message")
        create_comment(author=other_account, event=event, message="This is already hidden", hidden=True)

        self.login(account)
        self.get_url("activity_stream")

        self.assertTextPresent("This is a naughty message")
        self.assertTextAbsent("This is already hidden")
        self.click_and_confirm(".moderate-comment", wait_for_reload=False)

        # Test page
        self.wait_until(lambda d: not self.is_element_present(f"#comment-{c1.id}"))
        self.assertTextAbsent("This is a naughty message")

        # Test DB
        assert event.comments.get(id=c1.id).hidden


class CommentTests(AccountTestMixin, TestBase):
    def test_get_absolute_url(self):
        _, account = self.create_account()
        group = create_group()
        comment = create_comment(author=account, group=group)

        assert comment.get_absolute_url() == f"/groups/my-group/wall/?comment={comment.id}"

    def test_delete_wall_comment(self):
        _, account = self.create_account()
        group = create_group()
        comment = create_comment(author=account, group=group)
        related_events = [e for e in Event.objects.all() if e.get_comment() == comment]
        assert len(related_events) == 1

        comment.delete()
        related_events_2 = Event.objects.filter(id__in=[e.id for e in related_events])
        assert len(related_events_2) == 0

    def test_moderate_wall_comment(self):
        _, group_creator = self.create_account(username="group_creator")
        group = create_group(created_by=group_creator)

        _, account = self.create_account()
        comment = create_comment(author=account, group=group)

        events = [e for e in Event.objects.all() if e.get_comment() == comment]
        assert len(events) == 1
        (event,) = events

        hide_comment(comment.id)
        assert len([e for e in Event.objects.all() if e.get_comment() == comment]) == 0

    def test_visibility_for_hiding(self):
        event, _ = create_commentable_event()
        _, account = create_account()
        c = create_comment(event=event, author=account)

        moderation.hide_comment(c.id, by=create_account(is_moderator=True)[1])
        c.refresh_from_db()

        assert c not in Comment.objects.visible_for_account(account)
        assert not c.is_visible_for_account(account)

    def test_visibility_for_hellbanning(self):
        event, _ = create_commentable_event()
        _, hellbanned_account = create_account(is_hellbanned=True)
        c = create_comment(event=event, author=hellbanned_account)

        assert c in Comment.objects.visible_for_account(hellbanned_account)
        _, other_account = create_account(is_hellbanned=False)
        assert c not in Comment.objects.visible_for_account(other_account)

        assert c.is_visible_for_account(hellbanned_account)
        assert not c.is_visible_for_account(other_account)
