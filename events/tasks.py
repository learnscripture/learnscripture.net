from celery.task import task

from accounts.models import Account
from events.models import NewAccountEvent

@task(ignore_result=True)
def create_new_account_event(account_id):
    NewAccountEvent(account=Account.objects.get(id=account_id)).save()
