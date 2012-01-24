from django.db import models

from learnscripture.datastructures import make_choices


class BibleVersion(models.Model):
    short_name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.short_name

