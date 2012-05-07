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
def create_points_milestone_event(account_id, score_log_ids):
    account = Account.objects.get(id=account_id)
    try:
        total_score = account.total_score
    except (TotalScore.DoesNotExist, AttributeError):
        return

    # milestones are things like 1000, 2000 etc.  We can find these by
    # converting to strings and measuring different lengths or initial
    # characters.
    current_points = total_score.points
    if current_points < 1000:
        return

    previous_points = total_score.get_previous_points(score_log_ids)
    c_s = str(current_points)
    p_s = str(previous_points)

    if (len(p_s) < len(c_s) or p_s[0] != c_s[0]):
        # find most recent milestone crossed:
        points = int(c_s[0]) * 10 ** (len(c_s) - 1)
        PointsMilestoneEvent(account=account, points=points).save()
