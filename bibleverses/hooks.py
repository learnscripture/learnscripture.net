from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from bibleverses.models import QAPair, Verse
from bibleverses.services import get_search_service
from bibleverses.signals import verse_set_chosen
from bibleverses.tasks import fix_item_suggestions, verse_set_increase_popularity


def should_update_word_suggestions_on_save():
    return not (settings.TESTING or
                getattr(settings, 'LOADING_VERSES', False) or
                getattr(settings, 'LOADING_WORD_SUGGESTIONS', False))


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender, **kwargs):
    verse_set = sender
    verse_set_increase_popularity.delay(verse_set.id)


@receiver(post_save, sender=Verse)
def verse_saved(sender, **kwargs):
    verse = kwargs['instance']
    if should_update_word_suggestions_on_save():
        from bibleverses.suggestions import item_suggestions_need_updating
        # We definitely have text now, might not later,
        # so do this check at this point to avoid unnecessary
        # work and refetching the data from the API service
        if not item_suggestions_need_updating(verse):
            return
        fix_item_suggestions.apply_async([verse.version.slug, verse.reference],
                                         countdown=5)

        if get_search_service(verse.version.slug) is None:
            # No external search service, therefore must be using builtin DB
            # search, therefore need to update:
            Verse.objects.filter(id=verse.id).update_text_search()


@receiver(post_save, sender=QAPair)
def qapair_saved(sender, **kwargs):
    qapair = kwargs['instance']
    if should_update_word_suggestions_on_save():
        from bibleverses.suggestions import item_suggestions_need_updating
        if not item_suggestions_need_updating(qapair):
            return
        fix_item_suggestions.apply_async([qapair.catechism.slug, qapair.reference],
                                         countdown=5)
