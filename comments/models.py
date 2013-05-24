from django.db import models
from django.utils import timezone

from accounts.models import Account
from events.models import Event


class Comment(models.Model):
    author = models.ForeignKey(Account, related_name='comments')
    event = models.ForeignKey(Event, related_name='comments')
    created = models.DateTimeField(default=timezone.now)
    message = models.TextField()
