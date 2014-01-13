from celery.task import task
from django.db import models



@task(ignore_result=True)
def verse_set_increase_popularity(verse_set_id):
    from bibleverses.models import VerseSet
    VerseSet.objects.filter(id=verse_set_id).update(popularity=models.F('popularity') + 1)


