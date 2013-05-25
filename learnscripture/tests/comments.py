from __future__ import absolute_import

from comments.models import Comment
from events.models import Event, EventType

from .base import LiveServerTests


class AddCommentTests(LiveServerTests):

    def test_add_comment(self):
        identity, account = self.create_account()
        Event.objects.create(
            message_html="Test",
            event_type=EventType.POINTS_MILESTONE,
            account=account,
            event_data={},
            )

        message = "This is my comment"
        self.login(account)
        self.get_url('activity_stream')
        self.click('.show-add-comment')
        self.send_keys('#id-comment-box', message)
        self.click('#id-add-comment-btn')
        self.wait_for_ajax()

        # Test page
        self.assertIn("<p>%s</p>" % message, self.driver.page_source)

        # Test db
        c = Comment.objects.get()
        self.assertEqual(c.author, account)
        self.assertEqual(c.message, "This is my comment")
