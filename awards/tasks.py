from celery.task import task

from awards.models import StudentAward, MasterAward, Award, AwardType
from accounts.models import Account
from accounts.memorymodel import MM
from bibleverses.models import MemoryStage


@task(ignore_result=True)
def give_learning_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)
    started = account.identity.verse_statuses.filter(ignored=False,
                                                     memory_stage__gte=MemoryStage.TESTED)
    started_c = started.count()
    finished_c = started.filter(strength__gte=MM.LEARNT).count()

    for cls, count in [(StudentAward, started_c),
                       (MasterAward, finished_c)]:

        award_detail = cls(count=count)
        if award_detail.level > 0:
            award, new = Award.objects.get_or_create(
                account=account,
                award_type=cls.award_type,
                level=award_detail.level,
                )
