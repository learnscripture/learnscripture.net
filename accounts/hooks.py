from app_metrics.utils import metric
from django.dispatch import receiver

from accounts.signals import new_account, verse_started, verse_tested


@receiver(new_account)
def new_account_receiver(sender, **kwargs):
    metric('new_account')


@receiver(verse_started)
def verse_started_receiver(sender, **kwargs):
    metric('verse_started')


@receiver(verse_tested)
def verse_tested_receiver(sender, **kwargs):
    metric('verse_tested')

