from django.db.models.signals import post_save
from django.dispatch import receiver

from bibleverses.models import Verse, QAPair
from bibleverses.tasks import verse_set_increase_popularity, fix_item_suggestions
from bibleverses.signals import verse_set_chosen


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender, **kwargs):
    verse_set = sender
    verse_set_increase_popularity.delay(verse_set.id)

@receiver(post_save, sender=Verse)
def verse_saved(sender, **kwargs):
    verse = kwargs['instance']
    fix_item_suggestions(verse.version.slug, verse.reference)

@receiver(post_save, sender=QAPair)
def qapair_saved(sender, **kwargs):
    qapair = kwargs['instance']
    fix_item_suggestions(qapair.catechism.slug, qapair.reference)
