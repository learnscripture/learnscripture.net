from app_metrics.utils import metric
from django.dispatch import receiver

from accounts.signals import new_account


@receiver(new_account)
def new_account_receiver(sender, **kwargs):
    metric('new_account')
