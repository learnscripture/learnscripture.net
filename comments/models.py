from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.html import urlize, linebreaks

from accounts.models import Account
from events.models import Event

def format_comment_message(message):
    return mark_safe(linebreaks(mark_safe(urlize(message.strip(), autoescape=True)), autoescape=False))

class Comment(models.Model):
    author = models.ForeignKey(Account, related_name='comments')
    event = models.ForeignKey(Event, related_name='comments')
    created = models.DateTimeField(default=timezone.now)
    message = models.TextField()

    @property
    def message_formatted(self):
        return format_comment_message(self.message)
