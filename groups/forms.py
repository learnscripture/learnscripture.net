import selectable.forms.fields
from django import forms

from accounts.lookups import AccountLookup
from groups.models import Group


class EditGroupForm(forms.ModelForm):

    invited_users = selectable.forms.fields.AutoCompleteSelectMultipleField(
        lookup_class=AccountLookup,
        label='Invited users',
        required=False,
    )

    class Meta:
        model = Group
        fields = ('name', 'description', 'public', 'open', 'invited_users')

    def clean_name(self):
        name = self.cleaned_data['name']
        name = name.strip()
        if name == '':
            raise forms.ValidationError("This field is required")
        return name


f = EditGroupForm.base_fields['description'].widget.attrs
del f['cols']
f['rows'] = 3

EditGroupForm.base_fields['public'].help_text = """A public group is visible to everyone, and so is the member list. This can't be undone once selected."""
EditGroupForm.base_fields['open'].help_text = """Anyone can join an open group. For a closed group, you have to specifically invite people. A group must be public to be open."""
