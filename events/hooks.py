from django.dispatch import receiver

from awards.signals import new_award
import events.tasks

@receiver(new_award)
def new_award_receiver(sender, **kwargs):
    award = sender
    events.tasks.create_award_received_event.delay(award.id)
