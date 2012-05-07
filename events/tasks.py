from celery.task import task

from accounts.models import Account
from awards.models import Award
from bibleverses.models import VerseSet
from events.models import NewAccountEvent, AwardReceivedEvent, VerseSetCreatedEvent, StartedLearningVerseSetEvent


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
