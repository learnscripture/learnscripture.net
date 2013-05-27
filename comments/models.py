from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.html import urlize, linebreaks

from accounts.models import Account
from events.models import Event
from groups.models import Group


def format_comment_message(message):
    return mark_safe(linebreaks(mark_safe(urlize(message.strip(), autoescape=True)), autoescape=False))

class Comment(models.Model):
    author = models.ForeignKey(Account, related_name='comments')
    event = models.ForeignKey(Event, related_name='comments')
    group = models.ForeignKey(Group, null=True, blank=True,
                              related_name='comments')
    created = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    hidden = models.BooleanField(default=False, blank=True)

    @property
    def message_formatted(self):
        return format_comment_message(self.message)

    def __unicode__(self):
        return "%s: %s" % (self.id, self.message)

    def get_absolute_url(self):
        return self.event.get_absolute_url() + "#comment-%s" % self.id

import comments.hooks
