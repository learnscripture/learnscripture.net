from django.dispatch import receiver

from bibleverses.tasks import verse_set_increase_popularity
from bibleverses.signals import verse_set_chosen


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender, **kwargs):
    verse_set = sender
    verse_set_increase_popularity.delay(verse_set.id)
