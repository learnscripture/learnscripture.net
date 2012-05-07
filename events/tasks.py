from celery.task import task

from accounts.models import Account
from awards.models import Award
from bibleverses.models import VerseSet
from events.models import NewAccountEvent, AwardReceivedEvent, VerseSetCreatedEvent, StartedLearningVerseSetEvent, PointsMilestoneEvent, VersesStartedMilestoneEvent
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
    verse_set = VerseSet.objects.get(id=verse_set_id)
    if not verse_set.public:
        return
    StartedLearningVerseSetEvent(verse_set=verse_set,
                                 chosen_by=Account.objects.get(id=chosen_by_id)).save()



def crosses_milestone(previous_points, current_points):
    c_s = str(current_points)
    p_s = str(previous_points)

    if (len(p_s) < len(c_s) or p_s[0] != c_s[0]):
        # find most recent milestone crossed:
        points = int(c_s[0]) * 10 ** (len(c_s) - 1)
        return True, points
    else:
        return False, None


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
    m, points = crosses_milestone(previous_points, current_points)
    if m:
        PointsMilestoneEvent(account=account, points=points).save()


def is_milestone(c):
    c_s = str(c)
    return c_s.count('0') == len(c_s) - 1


@task(ignore_result=True)
def create_verses_started_milestone_event(account_id):
    account = Account.objects.get(id=account_id)

    # This could fail if the task gets delayed past the point where another
    # verse has been learnt. But we don't mind that much if some Events get
    # missed.
    c = account.identity.verse_statuses_started().count()

    if c > 9 and is_milestone(c):
        VersesStartedMilestoneEvent(account=account, verses_started=c).save()

