from django.db import models
from django.utils import timezone
from django.utils.html import linebreaks, urlize
from django.utils.safestring import mark_safe

from accounts.models import Account
from events.models import Event, get_absolute_url_for_event_comment, get_absolute_url_for_group_comment
from groups.models import Group


def format_comment_message(message):
    return mark_safe(linebreaks(mark_safe(urlize(message.strip(), autoescape=True)), autoescape=False))


COMMENT_MAX_LENGTH = 10000


class CommentQuerySet(models.QuerySet):
    def create(self, *, author: Account, **kwargs):
        if author.is_hellbanned:
            kwargs["author_was_hellbanned"] = True
        return super().create(author=author, **kwargs)

    def visible_for_account(self, account: Account):
        # See also Comment.is_visible_for_account
        qs = self.exclude(hidden=True).select_related("author")
        if account is None or not account.is_hellbanned:
            qs = qs.exclude(author_was_hellbanned=True)
        return qs


class CommentManager(models.Manager.from_queryset(CommentQuerySet)):
    pass


class Comment(models.Model):
    author = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="comments")
    # NB - this is the event the comment is attached to, if any,
    # not the 'NEW_COMMENT' event which is generated *about* this comment
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments", null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name="comments")
    created = models.DateTimeField(default=timezone.now)
    message = models.CharField(max_length=COMMENT_MAX_LENGTH)
    hidden = models.BooleanField(default=False, blank=True)
    author_was_hellbanned = models.BooleanField(default=False)

    objects = CommentManager()

    @property
    def message_formatted(self):
        return format_comment_message(self.message)

    def __str__(self):
        return f"{self.id}: {self.message}"

    def get_absolute_url(self):
        if self.event is not None:
            return get_absolute_url_for_event_comment(self.event, self.id)
        else:
            return get_absolute_url_for_group_comment(self.event, self.id, self.group.slug)

    def is_visible_for_account(self, account: Account) -> bool:
        # See also CommentQuerySet.visible_for_account
        if self.hidden:
            return False
        if account is None or not account.is_hellbanned:
            if self.author_was_hellbanned:
                return False
        return True


def hide_comment(comment_id):
    Comment.objects.filter(id=comment_id).update(hidden=True)
    # This deletion is less than ideal, but it is currently the easiest way to
    # get "group wall" comments (in contrast to event comments) to disappear
    # from the activity stream.
    # This moderation function is rarely needed in reality, and it's not a huge
    # issue if it is used inappropriately.

    delete_event_generated_for_comment(comment_id)


def delete_event_generated_for_comment(comment_id):
    Event.objects.filter(event_data__comment_id=comment_id).delete()
