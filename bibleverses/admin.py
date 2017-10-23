from django import forms
from django.contrib import admin

from .models import QAPair, TextVersion, UserVerseStatus, Verse, VerseChoice, VerseSet
from .parsing import InvalidVerseReference, parse_validated_internal_reference


class TextVersionAdmin(admin.ModelAdmin):
    list_display = ['short_name', 'slug', 'full_name', 'text_type', 'url']
    list_filter = ['language_code']


class VerseChoiceAdminForm(forms.ModelForm):
    def clean_internal_reference(self):
        ref = self.cleaned_data['internal_reference']
        try:
            parse_validated_internal_reference(ref)
        except InvalidVerseReference:
            raise forms.ValidationError("'%s' is not a valid internal verse reference." % ref)
        return ref

    class Meta:
        model = VerseChoice
        fields = '__all__'


class VerseSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'set_type', 'date_added', 'slug', 'created_by', 'description', 'additional_info']
    list_filter = ['set_type', 'public']
    search_fields = ['slug', 'name', 'description']


def mark_missing(modeladmin, request, queryset):
    for v in queryset:
        v.mark_missing()
mark_missing.short_description = "Mark selected verses as missing"  # noqa: E305


class VerseAdmin(admin.ModelAdmin):
    search_fields = ['localized_reference']
    list_display = ['localized_reference', 'version', 'missing']
    list_filter = ['version', 'missing']
    actions = [mark_missing]

    def get_queryset(self, request):
        return super(VerseAdmin, self).get_queryset(request).select_related('version')


class QAPairAdmin(admin.ModelAdmin):
    search_fields = ['localized_reference', 'question']
    list_display = ['localized_reference', 'question', 'catechism']
    list_filter = ['catechism']
    ordering = ['catechism', 'order']

    def get_queryset(self, request):
        return super(QAPairAdmin, self).get_queryset(request).select_related('catechism')


class UserVerseStatusAdmin(admin.ModelAdmin):
    search_fields = ['for_identity__account__username']
    list_filter = ['ignored']

    def username(obj):
        return obj.for_identity.account.username
    list_display = ['localized_reference', username, 'ignored']
    ordering = ['for_identity__account__username', 'localized_reference']

    def get_queryset(self, request):
        return super(UserVerseStatusAdmin, self).get_queryset(request).select_related('for_identity__account')


admin.site.register(TextVersion, TextVersionAdmin)
admin.site.register(VerseSet, VerseSetAdmin)
admin.site.register(Verse, VerseAdmin)
admin.site.register(QAPair, QAPairAdmin)
admin.site.register(UserVerseStatus, UserVerseStatusAdmin)
