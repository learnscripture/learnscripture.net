from django.contrib import admin

from .models import ModerationAction


class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ["id", "action_type", "group", "user", "done_at", "duration"]
    search_fields = ["group__name", "user__username"]
    ordering = ("-done_at",)
    autocomplete_fields = ["user", "group", "action_by"]

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("user", "group")


admin.site.register(ModerationAction, ModerationActionAdmin)
