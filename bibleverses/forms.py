from django import forms

from bibleverses.models import VerseSet


class VerseSetForm(forms.ModelForm):
    class Meta:
        model = VerseSet
        fields = ('name', 'description', 'additional_info', 'public')

    def clean_name(self):
        name = self.cleaned_data['name']
        name = name.strip()
        if name == '':
            raise forms.ValidationError("This field is required")
        return name

for n in ['description', 'additional_info']:
    f = VerseSetForm.base_fields[n].widget.attrs
    del f['cols']
    f['rows'] = 3
VerseSetForm.base_fields['public'].label="Make public (can't be undone)"
