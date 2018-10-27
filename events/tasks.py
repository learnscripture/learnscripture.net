from accounts.models import Account
from awards.models import Award
from bibleverses.models import TextVersion, VerseSet
from comments.models import Comment
from events.models import (AwardReceivedEvent, GroupCreatedEvent, GroupJoinedEvent, NewAccountEvent,
                           NewCommentEvent, PointsMilestoneEvent, StartedLearningCatechismEvent,
                           StartedLearningVerseSetEvent, VerseSetCreatedEvent, VersesFinishedMilestoneEvent,
                           VersesStartedMilestoneEvent)
from groups.models import Group
from learnscripture.celery import app


@app.task(ignore_result=True)
def create_new_account_event(account_id):
    NewAccountEvent(account=Account.objects.get(id=account_id)).save()


@app.task(ignore_result=True)
def create_award_received_event(award_id):
    AwardReceivedEvent(award=Award.objects.get(id=award_id)).save()


@app.task(ignore_result=True)
def create_new_verse_set_event(verse_set_id):
    VerseSetCreatedEvent(verse_set=VerseSet.objects.get(id=verse_set_id)).save()


@app.task(ignore_result=True)
def create_started_verse_set_event(verse_set_id, chosen_by_id):
    if chosen_by_id is None:
        # Not very interesting, don't bother with an event
        return
    verse_set = VerseSet.objects.get(id=verse_set_id)
    if not verse_set.public:
        return
    StartedLearningVerseSetEvent(verse_set=verse_set,
                                 chosen_by=Account.objects.get(id=chosen_by_id)).save()


@app.task(ignore_result=True)
def create_started_catechism_event(account_id, catechism_id):
    account = Account.objects.get(id=account_id)
    catechism = TextVersion.objects.get(id=catechism_id)
    StartedLearningCatechismEvent(account=account,
                                  catechism=catechism).save()


def crosses_milestone(previous_points, current_points):
    c_s = str(current_points)
    p_s = str(previous_points)

    if (len(p_s) < len(c_s) or p_s[0] != c_s[0]):
        # find most recent milestone crossed:
        points = int(c_s[0]) * 10 ** (len(c_s) - 1)
        return True, points
    else:
        return False, None


@app.task(ignore_result=True)
def create_points_milestone_event(account_id, previous_points, additional_points):
    account = Account.objects.get(id=account_id)

    # milestones are things like 1000, 2000 etc.  We can find these by
    # converting to strings and measuring different lengths or initial
    # characters.
    current_points = previous_points + additional_points
    if current_points < 1000:
        return

    m, points = crosses_milestone(int(previous_points), int(current_points))
    if m:
        PointsMilestoneEvent(account=account, points=points).save()


def is_milestone(c):
    c_s = str(c)
    return c_s.count('0') == len(c_s) - 1


@app.task(ignore_result=True)
def create_verses_started_milestone_event(account_id):
    account = Account.objects.get(id=account_id)

    # This could fail if the task gets delayed past the point where another
    # verse has been learnt. But we don't mind that much if some Events get
    # missed.
    c = account.identity.verses_started_count()

    if c > 9 and is_milestone(c):
        VersesStartedMilestoneEvent(account=account, verses_started=c).save()


@app.task(ignore_result=True)
def create_verses_finished_milestone_event(account_id):
    account = Account.objects.get(id=account_id)
    c = account.identity.verses_finished_count()
    if c > 9 and is_milestone(c):
        VersesFinishedMilestoneEvent(account=account, verses_finished=c).save()


@app.task(ignore_result=True)
def create_group_joined_event(group_id, account_id):
    account = Account.objects.get(id=account_id)
    group = Group.objects.get(id=group_id)

    if not group.public:
        return

    GroupJoinedEvent(account=account, group=group).save()


@app.task(ignore_result=True)
def create_group_created_event(group_id):
    group = Group.objects.get(id=group_id)
    account = group.created_by

    if not group.public:
        return

    GroupCreatedEvent(account=account, group=group).save()


@app.task(ignore_result=True)
def create_new_comment_event(comment_id):
    comment = Comment.objects.get(id=comment_id)
    account = comment.author

    # Hellbanning filtering - don't notify normal users of comments from
    # hellbanned users:
    if account.is_hellbanned:
        return

    NewCommentEvent(account=account, comment=comment).save()
