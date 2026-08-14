from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from common.utils.html import link

from .models import ModerationAction


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    def target(action: ModerationAction):
        obj = action.target
        content_type = ContentType.objects.get_for_model(obj.__class__)
        url = reverse(f"admin:{content_type.app_label}_{content_type.model}_change", args=[obj.pk])
        return link(url, str(obj))

    list_display = ["id", "action_type", target, "done_at", "duration"]
    search_fields = ["group__name", "user__username"]
    ordering = ("-done_at",)
    autocomplete_fields = ["user", "group", "comment", "action_by"]

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("user", "group", "comment")
