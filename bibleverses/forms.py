from django import forms

from bibleverses.models import VerseSet


class VerseSetForm(forms.ModelForm):
    class Meta:
        model = VerseSet
        fields = ('name', 'description', 'public')

    def clean_name(self):
        name = self.cleaned_data['name']
        name = name.strip()
        if name == '':
            raise forms.ValidationError("This field is required")
        return name

a = VerseSetForm.base_fields['description'].widget.attrs
del a['cols']
a['rows'] = 3
VerseSetForm.base_fields['public'].label="Make public (can't be undone)"
