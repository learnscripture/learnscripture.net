from celery.task import task

from awards.models import StudentAward, MasterAward, SharerAward, TrendSetterAward, AceAward
from accounts.models import Account
from accounts.memorymodel import MM
from bibleverses.models import MemoryStage, VerseSetType, VerseSet
from scores.models import ScoreReason


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
    return give_sharer_awards_func(account_id)


def give_sharer_awards_func(account_id):
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


@task(ignore_result=True)
def give_ace_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)

    test_reasons = [ScoreReason.VERSE_TESTED, ScoreReason.VERSE_REVISED]
    scores = account.score_logs.filter(reason__in=test_reasons).order_by('-created')

    try:
        last_score = scores.all()[0]
    except IndexError:
        return
    if last_score.accuracy != 1.0:
        return

    # Find the most recent score that *wasn't* 100%
    try:
        # Need to deal with NULLs in 'accuracy' field, due to old data.
        # If NULL, we assume it is *not* 100%
        breaker = (scores.filter(accuracy__isnull=True) | scores.filter(accuracy__lt=1.0))[0]
    except IndexError:
        breaker = None

    if breaker is None: # No break, everything recorded is at 100%
        count = scores.count()
    else:
        count = scores.filter(created__gt=breaker.created).count()

    AceAward(count=count).give_to(account)
