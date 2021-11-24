from django.conf import settings
from django.db import models
from django.utils import timezone


class SiteNoticeManager(models.Manager):
    def current(self, language_code):
        return self.get_queryset().filter(
            is_active=True, language_code=language_code, begins__lte=timezone.now(), ends__gt=timezone.now()
        )


class SiteNotice(models.Model):
    message_html = models.TextField()
    language_code = models.CharField(max_length=10, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)

    is_active = models.BooleanField(default=False)
    begins = models.DateTimeField()
    ends = models.DateTimeField()

    objects = SiteNoticeManager()

    def __str__(self):
        return self.message_html
