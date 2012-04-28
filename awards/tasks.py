from celery.task import task

from awards.models import StudentAward, Award, AwardType
from accounts.models import Account
from bibleverses.models import MemoryStage


@task(ignore_result=True)
def give_learning_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)
    started = account.identity.verse_statuses.filter(ignored=False,
                                                     memory_stage__gte=MemoryStage.TESTED)
    c = started.count()
    award_detail = StudentAward(count=c)
    if award_detail.level > 0:
        award, new = Award.objects.get_or_create(
            account=account,
            award_type=AwardType.STUDENT,
            level=award_detail.level,
            )
