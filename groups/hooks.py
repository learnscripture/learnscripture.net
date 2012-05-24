from django.db.models.signals import post_save

from .signals import group_joined
from .models import Membership

def membership_post_save_handler(sender, **kwargs):
    if kwargs.get('raw', False):
        return

    instance = kwargs['instance']
    if kwargs['created']:
        # new Membership object
        group_joined.send(sender=instance.group,
                          account=instance.account)

post_save.connect(membership_post_save_handler, sender=Membership)

