from django.dispatch import receiver

from awards.signals import new_award
from bibleverses.signals import verse_set_chosen
import events.tasks

@receiver(new_award)
def new_award_receiver(sender, **kwargs):
    award = sender
    events.tasks.create_award_received_event.delay(award.id)


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender=None, chosen_by=None, **kwargs):
    verse_set = sender
    chosen_by_id = None if chosen_by is None else chosen_by.id
    events.tasks.create_started_verse_set_event.apply_async([verse_set.id, chosen_by_id],
                                                            countdown=5)

