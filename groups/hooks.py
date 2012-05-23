from django.db.models.signals import pre_save

from .signals import group_joined
from .models import Membership

def membership_pre_save_handler(sender, **kwargs):
    if kwargs.get('raw', False):
        return

    instance = kwargs['instance']
    if instance.id is None:
        # new Membership object
        group_joined.send(sender=instance.group,
                          account=instance.account)

pre_save.connect(membership_pre_save_handler, sender=Membership)

