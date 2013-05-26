from __future__ import unicode_literals

from django.dispatch import receiver
from django.utils.html import format_html

from comments.signals import new_comment
from groups.signals import invitation_created
from learnscripture.templatetags.account_utils import account_link
from groups.utils import group_link

import accounts.tasks

@receiver(invitation_created)
def invitation_created_receiver(sender, **kwargs):
    invitation = sender
    msg = format_html("{0} invited you to join the group {1}",
                      account_link(invitation.created_by),
                      group_link(invitation.group))
    invitation.account.add_html_notice(msg)


@receiver(new_comment)
def new_comment_receiver(sender, **kwargs):
    comment = sender
    accounts.tasks.notify_account_about_comment.apply_async([comment.id],
                                                            countdown=5)
