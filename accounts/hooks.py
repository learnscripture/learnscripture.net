import django_ftl
from django.dispatch import receiver

import accounts.tasks
from comments.signals import new_comment
from groups.models import group_link
from groups.signals import invitation_created
from learnscripture.ftl_bundles import t
from learnscripture.templatetags.account_utils import account_link


@receiver(invitation_created)
def invitation_created_receiver(sender, **kwargs):
    invitation = sender
    receiver_account = invitation.account
    with django_ftl.override(receiver_account.default_language_code):
        msg = t(
            "accounts-invitation-received-html",
            dict(user=account_link(invitation.created_by), group=group_link(invitation.group)),
        )
        invitation.account.add_html_notice(msg)


@receiver(new_comment)
def new_comment_receiver(sender, **kwargs):
    comment = sender
    accounts.tasks.notify_account_about_comment.apply_async([comment.id])
