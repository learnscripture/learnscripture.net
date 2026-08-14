from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["id", "account", "event_type", "weight", "created"]
    list_filter = ["event_type"]
    raw_id_fields = ["parent_event"]
    autocomplete_fields = ["account", "group"]

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("account")
