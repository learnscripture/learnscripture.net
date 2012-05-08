from django.contrib import admin

from .models import Event

class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_type', 'weight', 'created')

admin.site.register(Event, EventAdmin)
