from celery.task import task

from accounts.models import Account

@task
def give_student_award(account_id):
    account = Account.objects.get(id=account_id)
