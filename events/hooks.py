from django.dispatch import receiver

from accounts.signals import new_account
from awards.signals import new_award, lost_award
from bibleverses.signals import verse_set_chosen
import events.tasks

@receiver(new_award)
def new_award_receiver(sender, **kwargs):
    award = sender
    events.tasks.create_award_received_event.delay(award.id)


@receiver(lost_award)
def lost_award_receiver(sender, **kwargs):
    award = sender
    # Since this is called when an award is deleted,
    # we have to call immediately, not via the queue.
    events.tasks.create_award_lost_event(award)


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender=None, chosen_by=None, **kwargs):
    verse_set = sender
    chosen_by_id = None if chosen_by is None else chosen_by.id
    events.tasks.create_started_verse_set_event.apply_async([verse_set.id, chosen_by_id],
                                                            countdown=5)


@receiver(new_account)
def new_account_receiver(sender, **kwargs):
    account = sender
    events.tasks.create_new_account_event.apply_async([account.id], countdown=5)
