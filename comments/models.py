from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.html import urlize, linebreaks, format_html

from accounts.models import Account
from events.models import Event
from groups.models import Group
from groups.utils import group_link
from learnscripture.templatetags.account_utils import account_link


def format_comment_message(message):
    return mark_safe(linebreaks(mark_safe(urlize(message.strip(), autoescape=True)), autoescape=False))


class Comment(models.Model):
    author = models.ForeignKey(Account, related_name='comments')
    # NB - this is the event the comment is attached to, if any,
    # not the 'NEW_COMMENT' event which is generated *about* this comment
    event = models.ForeignKey(Event, related_name='comments',
                              null=True, blank=True)
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
        if self.event is not None:
            return self.event.get_absolute_url() + "#comment-%s" % self.id
        else:
            return reverse('group_wall', args=(self.group.slug,)) + "?comment=%s" % self.id

    def get_subject_html(self):
        """
        Returns a desription of what the comment is attached to, as HTML fragment
        """
        if self.event is not None:
            return format_html("{0}'s activity", account_link(self.event.account))
        elif self.group is not None:
            return format_html("{0}'s wall", group_link(self.group))


from comments import hooks  # NOQA
