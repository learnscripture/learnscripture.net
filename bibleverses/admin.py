from django.contrib import admin
from django import forms

from .models import TextVersion, Verse, VerseSet, VerseChoice, QAPair


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


class QAPairAdmin(admin.ModelAdmin):
    search_fields = ['reference', 'question']
    list_display = ['reference', 'question', 'catechism']
    list_filter = ['catechism']
    ordering = ['catechism', 'order']

    def queryset(self, request):
        return super(QAPairAdmin, self).queryset(request).select_related('catechism')

admin.site.register(TextVersion)
admin.site.register(VerseSet, VerseSetAdmin)
admin.site.register(Verse, VerseAdmin)
admin.site.register(QAPair, QAPairAdmin)
