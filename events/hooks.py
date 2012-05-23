from django.dispatch import receiver

from accounts.signals import new_account, verse_started, points_increase
from awards.signals import new_award, lost_award
from bibleverses.signals import verse_set_chosen, public_verse_set_created
import events.tasks
from groups.signals import group_joined


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


@receiver(verse_started)
def verse_started_receiver(sender, **kwargs):
    account = sender
    events.tasks.create_verses_started_milestone_event.apply_async([account.id],
                                                                   countdown=2)


@receiver(points_increase)
def points_increase_receiver(sender=None, previous_points=None, points_added=None, **kwargs):
    account = sender
    events.tasks.create_points_milestone_event.apply_async([account.id,
                                                           previous_points,
                                                           points_added],
                                                          countdown=5)


@receiver(public_verse_set_created)
def public_verse_set_created_receiver(sender, **kwargs):
    verse_set = sender
    events.tasks.create_new_verse_set_event.apply_async([verse_set.id],
                                                        countdown=5)


@receiver(group_joined)
def group_joined_receiver(sender, account=None, **kwargs):
    group = sender
    events.tasks.create_group_joined_event.apply_async([group.id, account.id],
                                                       countdown=5)
