from django.db import models
from django.utils import timezone


class SiteNoticeManager(models.Manager):

    def current(self):
        return self.get_queryset().filter(is_active=True,
                                          begins__lte=timezone.now(),
                                          ends__gt=timezone.now())


class SiteNotice(models.Model):
    message_html = models.TextField()
    is_active = models.BooleanField(default=False)
    begins = models.DateTimeField()
    ends = models.DateTimeField()

    objects = SiteNoticeManager()

    def __str__(self):
        return self.message_html
