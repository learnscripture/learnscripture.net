from django.dispatch import receiver

from groups.signals import invitation_created
from learnscripture.templatetags.account_utils import account_link, group_link


@receiver(invitation_created)
def invitation_created_receiver(sender, **kwargs):
    invitation = sender
    msg = (u"""%s invited you to join the group %s""" %
           (account_link(invitation.created_by),
            group_link(invitation.group)))
    invitation.account.add_html_notice(msg)
