from datetime import timedelta

from accounts.models import Account, Identity, get_verse_started_running_streaks
from awards.models import (AceAward, AddictAward, ConsistentLearnerAward, MasterAward, OrganizerAward, RecruiterAward,
                           SharerAward, StudentAward, TrendSetterAward)
from bibleverses.models import VerseSet, VerseSetType
from groups.models import combined_membership_count_for_creator
from learnscripture.utils.tasks import task
from scores.models import ScoreReason, get_number_of_distinct_hours_for_account_id


@task
def give_learning_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)

    started_c = account.identity.verses_started_count()
    finished_c = account.identity.verses_finished_count()

    for cls, count in [(StudentAward, started_c),
                       (MasterAward, finished_c)]:

        cls(count=count).give_to(account)


@task
def give_sharer_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)
    c = account.verse_sets_created.public().filter(set_type=VerseSetType.SELECTION).count()
    SharerAward(count=c).give_to(account)


@task
def give_verse_set_used_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)

    verse_set_ids = list(account.verse_sets_created.public().values_list('id', flat=True))

    c = VerseSet.objects.popularity_for_sets(verse_set_ids, [account_id])
    TrendSetterAward(count=c).give_to(account)


@task
def give_ace_awards(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)

    test_reasons = [ScoreReason.VERSE_TESTED, ScoreReason.VERSE_REVIEWED]
    actions = account.action_logs.filter(reason__in=test_reasons).order_by('-created')

    try:
        last_action = actions.all()[0]
    except IndexError:
        return
    if last_action.accuracy != 1.0:
        return

    # Find the most recent score that *wasn't* 100%
    try:
        # Need to deal with NULLs in 'accuracy' field, due to old data.
        # If NULL, we assume it is *not* 100%
        breaker = (actions.filter(accuracy__isnull=True) | actions.filter(accuracy__lt=1.0))[0]
    except IndexError:
        breaker = None

    if breaker is None:  # No break, everything recorded is at 100%
        count = actions.count()
    else:
        count = actions.filter(created__gt=breaker.created).count()

    AceAward(count=count).give_to(account)


@task
def give_recruiter_award(account_id):
    if account_id is None:
        return
    account = Account.objects.get(id=account_id)

    count = Identity.objects.filter(account__isnull=False,
                                    referred_by=account).count()
    RecruiterAward(count=count).give_to(account)


def give_all_addict_awards():
    for account in Account.objects.active().all():
        give_addict_award.apply_async([account.id])


@task
def give_addict_award(account_id):
    if get_number_of_distinct_hours_for_account_id(account_id) == 24:
        AddictAward().give_to(Account.objects.get(id=account_id))


@task
def give_organizer_awards(account_id):
    count = combined_membership_count_for_creator(account_id)
    OrganizerAward(count=count).give_to(Account.objects.get(id=account_id))


def give_all_consistent_learner_awards():
    min_days = min(ConsistentLearnerAward.DAYS.values())
    for account_id, streak in get_verse_started_running_streaks().items():
        if streak >= min_days:
            give_consistent_learner_award.apply_async([account_id, streak])


@task
def give_consistent_learner_award(account_id, streak):
    ConsistentLearnerAward(time_period=timedelta(days=streak)).give_to(Account.objects.get(id=account_id))
