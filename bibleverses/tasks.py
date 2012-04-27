from celery.task import task
from django.db import models

from bibleverses.models import VerseSet


@task(ignore_result=True)
def verse_set_increase_popularity(verse_set_id):
    VerseSet.objects.filter(id=verse_set_id).update(popularity=models.F('popularity') + 1)


