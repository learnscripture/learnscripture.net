from django.contrib import admin
from django import forms

from .models import BibleVersion, Verse, VerseSet, VerseChoice


class VerseChoiceAdminForm(forms.ModelForm):
    def clean_reference(self):
        ref = self.cleaned_data['reference']
        if not Verse.objects.filter(reference=ref).exists():
            raise forms.ValidationError("'%s' is not a valid verse." % ref)
        return ref

    class Meta:
        model = VerseChoice


class VerseSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'set_type']
    list_filter = ['set_type']


class VerseAdmin(admin.ModelAdmin):
    search_fields = ['reference']
    list_display = ['reference', 'version']
    list_filter = ['version']

    def queryset(self, request):
        return super(VerseAdmin, self).queryset(request).select_related('version')


admin.site.register(BibleVersion)
admin.site.register(VerseSet, VerseSetAdmin)
admin.site.register(Verse, VerseAdmin)
