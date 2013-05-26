from __future__ import unicode_literals

from django.dispatch import receiver
from django.utils.html import format_html

from comments.signals import new_comment
from groups.signals import invitation_created
from learnscripture.templatetags.account_utils import account_link
from groups.utils import group_link


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
    event = comment.event
    # Notify the account that generated the event
    account = event.account

    # But not if it is the author:
    if account == comment.author:
        return

    # And not if commenter is hellbanned:
    if comment.author.is_hellbanned and not account.is_hellbanned:
        return

    # And not if they already have a notice about it.
    if account.identity.notices.filter(
        related_event=event,
        ).exists():
        return

    msg = format_html('You have new comments on <b><a href="{0}">your event</a></b> "{1}"',
                      event.get_absolute_url(),
                      event.render_html()
                      )

    notice = account.add_html_notice(msg)
    notice.related_event = event
    notice.save()
