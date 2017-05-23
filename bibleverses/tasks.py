from django.db import models

from learnscripture.celery import app


@app.task(ignore_result=True)
def verse_set_increase_popularity(verse_set_id):
    from bibleverses.models import VerseSet
    VerseSet.objects.filter(id=verse_set_id).update(popularity=models.F('popularity') + 1)


@app.task(ignore_result=True)
def fix_item_suggestions(version_slug, reference):
    from bibleverses.suggestions import fix_item
    fix_item(version_slug, reference)
