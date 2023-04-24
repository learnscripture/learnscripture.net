from datetime import timedelta

from django.db import models
from django.db.models.enums import TextChoices
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.functional import cached_property

from accounts.models import Account
from comments.models import Comment
from comments.models import hide_comment as comments_hide_comment
from groups.models import Group


class ModerationActionType(TextChoices):
    GROUP_QUIETENED = "group_quietened", "Group quietened"
    GROUP_UNQUIETENED = "group_unquietened", "Group unquietened"
    USER_HELLBANNED = "user_hellbanned", "User hellbanned"
    USER_UNHELLBANNED = "user_unhellbanned", "User unhellbanned"
    COMMENT_HIDDEN = "comment_hidden", "Comment hidden"


class ModerationActionQuerySet(models.QuerySet):
    def create(self, **kwargs):
        # First cancel any previous of the same type
        same_type_kwargs = {k: v for k, v in kwargs.items() if k in ("action_type", "group", "user")}
        self.filter(**same_type_kwargs).reversible().update(reversal_cancelled=True)
        # Then create
        return super().create(**kwargs)

    def hellbans(self):
        return self.filter(action_type=ModerationActionType.USER_HELLBANNED)

    def temporary(self):
        return self.filter(
            duration__isnull=False,
        )

    def reversible(self):
        return self.temporary().filter(
            reversed_at__isnull=True,
            reversal_cancelled=False,
        )

    def to_reverse_now(self):
        return (
            self.reversible()
            .annotate(reversal_due_at=models.F("done_at") + models.F("duration"))
            .filter(reversal_due_at__lt=timezone.now())
        )


class ModerationAction(models.Model):
    action_by = models.ForeignKey(Account, related_name="moderation_actions_taken", on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50, choices=ModerationActionType.choices)

    # Target: Only one of the following should be non-null:
    group = models.ForeignKey(Group, null=True, blank=True, related_name="moderation_actions", on_delete=models.CASCADE)
    user = models.ForeignKey(
        Account, null=True, blank=True, related_name="moderation_actions", on_delete=models.CASCADE
    )
    comment = models.ForeignKey(
        Comment, null=True, blank=True, related_name="moderation_actions", on_delete=models.CASCADE
    )

    done_at = models.DateTimeField(default=timezone.now)
    duration = models.DurationField(default=None, null=True, blank=True)  # None for indefinite
    reversed_at = models.DateTimeField(null=True, default=None, blank=True)  # Set when reversal done
    reversal_cancelled = models.BooleanField(default=False)  # Set True if reversal is cancelled

    objects = models.Manager.from_queryset(ModerationActionQuerySet)()

    def __str__(self):
        return f"Moderation {self.id}, {self.get_action_type_display()}: {self.target}"

    @property
    def target(self) -> Account | Group:
        if self.group_id is not None:
            return self.group
        elif self.user_id is not None:
            return self.user
        elif self.comment_id is not None:
            return self.comment

    @cached_property  # cached_property enables setting, so it works with annotate above
    def reversal_due_at(self):
        return self.done_at + self.duration

    @atomic
    def reverse(self):
        if self.action_type == ModerationActionType.USER_HELLBANNED:
            self.user.unhellban()
        elif self.action_type == ModerationActionType.GROUP_QUIETENED:
            self.group.unquieten()
        else:
            raise NotImplementedError(f"reverse not implemented for {self.action_type}")
        self.reversed_at = timezone.now()
        self.save()


@atomic
def quieten_group(group: Group, by: Account):
    group.quieten()
    group.moderation_actions.create(action_by=by, action_type=ModerationActionType.GROUP_QUIETENED)


@atomic
def unquieten_group(group: Group, by: Account):
    group.unquieten()
    group.moderation_actions.create(action_by=by, action_type=ModerationActionType.GROUP_UNQUIETENED)


@atomic
def hellban_user(user: Account, *, by: Account, duration: None | timedelta):
    user.hellban()
    user.moderation_actions.create(action_by=by, action_type=ModerationActionType.USER_HELLBANNED, duration=duration)


@atomic
def unhellban_user(user: Account, *, by: Account):
    user.unhellban()
    user.moderation_actions.create(action_by=by, action_type=ModerationActionType.USER_UNHELLBANNED)


@atomic
def hide_comment(comment_id: int, *, by: Account):
    comments_hide_comment(comment_id)
    ModerationAction.objects.create(
        comment_id=comment_id, action_by=by, action_type=ModerationActionType.COMMENT_HIDDEN
    )


def run_moderation_adjustments():
    for action in ModerationAction.objects.to_reverse_now():
        action.reverse()
