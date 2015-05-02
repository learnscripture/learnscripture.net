from __future__ import absolute_import

import time

from autofixture import AutoFixture
from django.test import TestCase

from comments.models import Comment
from events.models import Event, EventType
from groups.models import Group

from .base import FullBrowserTest, AccountTestMixin


class CommentPageTests(FullBrowserTest):

    def setUp(self):
        super(CommentPageTests, self).setUp()
        self.event_identity, self.event_account = \
            self.create_account(username="eventaccount",
                                email="eventaccount@a.com")
        self.identity, self.account = self.create_account()
        self.event = Event.objects.create(
            message_html="Test",
            event_type=EventType.POINTS_MILESTONE,
            account=self.event_account,
            event_data={},
        )

    def test_add_comment(self):
        self.event_identity.notices.all().delete()

        message = "This is my comment"
        self.login(self.account)
        self.get_url('activity_stream')
        self.click('.show-add-comment')
        self.send_keys('#id-comment-box', message)
        self.click('#id-add-comment-btn')

        # Test page
        self.assertIn("<p>%s</p>" % message, self.driver.page_source)

        # Test db
        c = Comment.objects.get()
        self.assertEqual(c.author, self.account)
        self.assertEqual(c.message, "This is my comment")

        # Test event created
        self.assertEqual(Event.objects.filter(parent_event=self.event,
                                              event_type=EventType.NEW_COMMENT,
                                              account=self.account).count(),
                         1)

        # Test notice created
        self.assertEqual(self.event_identity.notices.filter(related_event=self.event).count(),
                         1)

    def test_no_event_from_hellbanned_users(self):

        self.account.is_hellbanned = True
        self.account.save()
        message = "This is my comment"
        self.login(self.account)
        self.get_url('activity_stream')
        self.click('.show-add-comment')
        self.send_keys('#id-comment-box', message)
        self.click('#id-add-comment-btn')
        time.sleep(1)

        # Test db - user should be able to see own message
        c = Comment.objects.get()
        self.assertEqual(c.author, self.account)
        self.assertEqual(c.message, "This is my comment")

        # Test event NOT created
        self.assertEqual(Event.objects.filter(parent_event=self.event,
                                              event_type=EventType.NEW_COMMENT,
                                              account=self.account).count(),
                         0)

    def test_moderate_comment(self):
        other_identity, other_account = self.create_account(username="other",
                                                            email="other@other.com")
        self.account.is_moderator = True
        self.account.save()
        c1 = self.event.comments.create(
            message="This is a naughty message",
            author=other_account,
        )
        self.event.comments.create(
            message="This is already hidden",
            author=other_account,
            hidden=True
        )

        self.login(self.account)
        self.get_url('activity_stream')

        self.assertIn("This is a naughty message", self.driver.page_source)
        self.assertNotIn("This is already hidden", self.driver.page_source)
        self.click('.moderate-comment', produces_alert=True)
        self.confirm()
        self.wait_for_ajax()
        time.sleep(1)

        # Test page
        self.assertNotIn("This is a naughty message", self.driver.page_source)

        # Test DB
        self.assertEqual(self.event.comments.get(id=c1.id).hidden, True)


class CommentTests(AccountTestMixin, TestCase):
    def test_get_absolute_url(self):
        _, account = self.create_account()
        group = AutoFixture(Group,
                            field_values={'slug': 'my-group'},
                            ).create_one()
        comment = Comment.objects.create(
            author=account,
            message="Hello",
            group=group)

        self.assertEqual(comment.get_absolute_url(),
                         "/groups/my-group/wall/?comment=%s" % comment.id)
