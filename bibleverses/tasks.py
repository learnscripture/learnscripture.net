from django.db import models

from learnscripture.utils.tasks import task


@task
def verse_set_increase_popularity(verse_set_id):
    from bibleverses.models import VerseSet
    VerseSet.objects.filter(id=verse_set_id).update(popularity=models.F('popularity') + 1)


@task
def fix_item_suggestions(version_slug, localized_reference, text_saved):
    from bibleverses.suggestions.modelapi import fix_item
    fix_item(version_slug, localized_reference, text_saved)
