from django import forms

from bibleverses.models import VerseSet
from learnscripture.ftl_bundles import t


class VerseSetForm(forms.ModelForm):
    class Meta:
        model = VerseSet
        fields = ['name', 'description', 'additional_info', 'public', 'language_code']

    def clean_name(self):
        name = self.cleaned_data['name']
        name = name.strip()
        if name == '':
            raise forms.ValidationError(t('forms-field-required'))
        return name


for n in ['description', 'additional_info']:
    f = VerseSetForm.base_fields[n].widget.attrs
    del f['cols']
    f['rows'] = 3
