from celery.task import task

from accounts.models import Account
from awards.models import Award
from bibleverses.models import VerseSet
from events.models import NewAccountEvent, AwardReceivedEvent, VerseSetCreatedEvent, StartedLearningVerseSetEvent, PointsMilestoneEvent
from scores.models import TotalScore


@task(ignore_result=True)
def create_new_account_event(account_id):
    NewAccountEvent(account=Account.objects.get(id=account_id)).save()


@task(ignore_result=True)
def create_award_received_event(award_id):
    AwardReceivedEvent(award=Award.objects.get(id=award_id)).save()


@task(ignore_result=True)
def create_new_verse_set_event(verse_set_id):
    VerseSetCreatedEvent(verse_set=VerseSet.objects.get(id=verse_set_id)).save()


@task(ignore_result=True)
def create_started_verse_set_event(verse_set_id, chosen_by_id):
    if chosen_by_id is None:
        # Not very interesting, don't bother with an event
        return
    StartedLearningVerseSetEvent(verse_set=VerseSet.objects.get(id=verse_set_id),
                                 chosen_by=Account.objects.get(id=chosen_by_id)).save()


@task(ignore_result=True)
def create_points_milestone_event(account_id):
    account = Account.objects.get(id=account_id)
    try:
        total_score = account.total_score.points
        last_score = account.score_logs.order_by('-created')[0]
    except (TotalScore.DoesNotExist, AttributeError, IndexError):
        return

    previous_score = total_score - last_score.points

    # milestones are things like 1000, 2000 etc.  We can find these by
    # converting to strings and measuring different lengths or initial
    # characters.
    if total_score < 1000:
        return

    p_s = str(previous_score)
    t_s = str(total_score)

    if (len(p_s) < len(t_s) or p_s[0] != t_s[0]):
        # find most recent milestone crossed:
        points = int(t_s[0]) * 10 ** (len(t_s) - 1)
        PointsMilestoneEvent(account=account, points=points).save()
