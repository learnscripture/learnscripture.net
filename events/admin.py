from django.contrib import admin

from .models import Event

class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'event_type', 'weight', 'created')

    def queryset(self, *args, **kwargs):
        return super(EventAdmin, self).queryset(*args, **kwargs).select_related('account')

admin.site.register(Event, EventAdmin)
