from django.dispatch import receiver

from bibleverses.tasks import verse_set_increase_popularity
from bibleverses.signals import verse_set_chosen


@receiver(verse_set_chosen)
def _verse_set_chosen(sender, **kwargs):
    verse_set = sender
    from awards.tasks import give_verse_set_used_awards
    give_verse_set_used_awards.delay(verse_set.created_by_id)
    verse_set_increase_popularity.delay(verse_set.id)
