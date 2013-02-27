from django.db import models
from django.utils import timezone

import learnscripture.hooks


class SiteNoticeManager(models.Manager):

    def current(self):
        return self.get_query_set().filter(is_active=True,
                                           begins__lte=timezone.now(),
                                           ends__gt=timezone.now())

class SiteNotice(models.Model):
    message_html = models.TextField()
    is_active = models.BooleanField()
    begins = models.DateTimeField()
    ends = models.DateTimeField()

    objects = SiteNoticeManager()

    def __unicode__(self):
        return self.message_html
