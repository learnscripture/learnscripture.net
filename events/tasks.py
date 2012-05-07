from celery.task import task

from accounts.models import Account
from awards.models import Award
from events.models import NewAccountEvent, AwardReceivedEvent


@task(ignore_result=True)
def create_new_account_event(account_id):
    NewAccountEvent(account=Account.objects.get(id=account_id)).save()


@task(ignore_result=True)
def create_award_received_event(award_id):
    AwardReceivedEvent(award=Award.objects.get(id=award_id)).save()
