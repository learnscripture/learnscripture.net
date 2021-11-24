from django.db.models.signals import post_save

from .models import Invitation, Membership
from .signals import group_joined, invitation_created


def membership_post_save_handler(sender, **kwargs):
    if kwargs.get("raw", False):
        return

    instance = kwargs["instance"]
    if kwargs["created"]:
        # new Membership object
        group_joined.send(sender=instance.group, account=instance.account)


def invitation_post_save_handler(sender, **kwargs):
    if kwargs.get("raw", False):
        return

    if kwargs["created"]:
        invitation_created.send(sender=kwargs["instance"])


post_save.connect(membership_post_save_handler, sender=Membership)
post_save.connect(invitation_post_save_handler, sender=Invitation)
