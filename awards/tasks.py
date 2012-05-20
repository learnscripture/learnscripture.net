from datetime import timedelta

from celery.task import task
from django.utils import timezone

from awards.models import AwardType, Award, StudentAward, MasterAward, SharerAward, TrendSetterAward, AceAward, RecruiterAward, ReigningWeeklyChampion, WeeklyChampion
from accounts.models import Account, Identity
from accounts.memorymodel import MM
from bibleverses.models import MemoryStage, VerseSetType, VerseSet
from scores.models import ScoreReason, get_leaderboard_since

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


@task(ignore_result=True)
def give_recruiter_award(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)

    count = Identity.objects.filter(account__isnull=False,
                                    referred_by=account).count()
    RecruiterAward(count=count).give_to(account)


@task(ignore_result=True)
def give_champion_awards():
    now = timezone.now()
    # Reigning weekly champion:
    champion_id = get_leaderboard_since(now - timedelta(days=7), 0, 1)[0]['account_id']
    champion = Account.objects.get(id=champion_id)
    old_champions = set([a.account for a in (Award.objects
                                             .filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
                                             .select_related('account'))
                         ])

    # old_champions should only contain 1 item, but DB doesn't guarantee that,
    # so we cope with errors here by assuming multiple old champions

    champions_to_remove = set(old_champions) - set([champion])
    continuing_champions = old_champions & set([champion])

    if champion not in old_champions:
        # New champion
        ReigningWeeklyChampion().give_to(champion)
        WeeklyChampion(level=1).give_to(champion)

    for account in champions_to_remove:
        for award in account.awards.filter(award_type=AwardType.REIGNING_WEEKLY_CHAMPION):
            award.delete()

    for account in continuing_champions:
        # We can calculate how long they've had it using Award.created for the
        # 'reigning' award, and level them up if necessary
        existing_award = account.awards.get(award_type=AwardType.REIGNING_WEEKLY_CHAMPION)
        WeeklyChampion(time_period=now - existing_award.created).give_to(account)
