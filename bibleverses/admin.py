from django.contrib import admin

from .models import BibleVersion, Verse, VerseSet, VerseChoice


class VerseChoiceInline(admin.TabularInline):
    model = VerseChoice


class VerseSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'set_type']
    list_filter = ['set_type']

    inlines = [
        VerseChoiceInline
        ]


class VerseAdmin(admin.ModelAdmin):
    search_fields = ['reference']
    list_display = ['reference', 'version']
    list_filter = ['version']

    def queryset(self, request):
        return super(VerseAdmin, self).queryset(request).select_related('version')


admin.site.register(BibleVersion)
admin.site.register(VerseSet, VerseSetAdmin)
admin.site.register(Verse, VerseAdmin)
