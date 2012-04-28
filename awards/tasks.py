from celery.task import task

from awards.models import StudentAward, MasterAward, SharerAward, TrendSetterAward, Award, AwardType
from accounts.models import Account
from accounts.memorymodel import MM
from bibleverses.models import MemoryStage, VerseSetType, VerseSet


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

        cls(count=count).give_to(account)


@task(ignore_result=True)
def give_sharer_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)
    c = account.verse_sets_created.filter(public=True, set_type=VerseSetType.SELECTION).count()
    SharerAward(count=c).give_to(account)


@task(ignore_result=True)
def give_verse_set_used_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)

    verse_set_ids = list(account.verse_sets_created.filter(public=True).values_list('id', flat=True))

    c = VerseSet.objects.popularity_for_sets(verse_set_ids, [account_id])
    TrendSetterAward(count=c).give_to(account)
