from django.conf import settings

from django.db.models.signals import post_save
from django.dispatch import receiver

from bibleverses.models import Verse, QAPair
from bibleverses.tasks import verse_set_increase_popularity, fix_item_suggestions
from bibleverses.signals import verse_set_chosen


def should_update_word_suggestions():
    return not (settings.TESTING or getattr(settings, 'LOADING_VERSES', False))


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender, **kwargs):
    verse_set = sender
    verse_set_increase_popularity.delay(verse_set.id)


@receiver(post_save, sender=Verse)
def verse_saved(sender, **kwargs):
    verse = kwargs['instance']
    if should_update_word_suggestions():
        fix_item_suggestions.delay(verse.version.slug, verse.reference)


@receiver(post_save, sender=QAPair)
def qapair_saved(sender, **kwargs):
    qapair = kwargs['instance']
    if should_update_word_suggestions():
        fix_item_suggestions.delay(qapair.catechism.slug, qapair.reference)
