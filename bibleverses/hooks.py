from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from bibleverses.models import QAPair, Verse
from bibleverses.signals import verse_set_chosen
from bibleverses.tasks import fix_item_suggestions, verse_set_increase_popularity


def should_update_word_suggestions_on_save():
    return not (settings.TESTS_RUNNING or
                getattr(settings, 'LOADING_VERSES', False) or
                getattr(settings, 'LOADING_WORD_SUGGESTIONS', False))


def should_update_text_search_on_save():
    # Happens to use the same criteria
    return should_update_word_suggestions_on_save()


@receiver(verse_set_chosen)
def verse_set_chosen_receiver(sender, **kwargs):
    verse_set = sender
    verse_set_increase_popularity.delay(verse_set.id)


@receiver(post_save, sender=Verse)
def verse_saved_update_word_suggestions(sender, **kwargs):
    from bibleverses.suggestions.modelapi import item_suggestions_need_updating
    verse = kwargs['instance']
    if not should_update_word_suggestions_on_save():
        return

    if verse.text_saved == "":
        return

    # We definitely have text now, might not later, so do this check at this
    # point to avoid unnecessary work and refetching the data from the API
    # service
    if not item_suggestions_need_updating(verse):
        return

    fix_item_suggestions.apply_async([verse.version.slug, verse.localized_reference, verse.text_saved],
                                     countdown=5)


@receiver(post_save, sender=Verse)
def verse_saved_update_text_search(sender, **kwargs):
    verse = kwargs['instance']
    if not should_update_text_search_on_save():
        return

    if verse.version.db_based_searching:
        # No external search service, therefore must be using builtin DB
        # search, therefore need to update:
        verse.version.update_text_search(Verse.objects.filter(id=verse.id))


@receiver(post_save, sender=QAPair)
def qapair_saved(sender, **kwargs):
    qapair = kwargs['instance']
    if should_update_word_suggestions_on_save():
        from bibleverses.suggestions.modelapi import item_suggestions_need_updating
        if not item_suggestions_need_updating(qapair):
            return
        fix_item_suggestions.apply_async([qapair.catechism.slug, qapair.localized_reference, None],
                                         countdown=5)
