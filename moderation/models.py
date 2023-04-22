from django.db import models
from django.db.models.enums import TextChoices
from django.utils import timezone

from accounts.models import Account
from groups.models import Group


class ModerationActionType(TextChoices):
    GROUP_QUIETENED = "group_quietened", "Group quietened"
    GROUP_UNQUIETENED = "group_unquietened", "Group unquietened"


class ModerationAction(models.Model):
    action_by = models.ForeignKey(Account, related_name="moderation_actions_taken", on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50, choices=ModerationActionType.choices)
    group = models.ForeignKey(Group, null=True, blank=True, related_name="moderation_actions", on_delete=models.CASCADE)
    done_at = models.DateTimeField(default=timezone.now)


def quieten_group(group: Group, by: Account):
    group.quieten()
    group.moderation_actions.create(action_by=by, action_type=ModerationActionType.GROUP_QUIETENED)


def unquieten_group(group: Group, by: Account):
    group.unquieten()
    group.moderation_actions.create(action_by=by, action_type=ModerationActionType.GROUP_UNQUIETENED)
