from dal import autocomplete
from django import forms

from accounts.models import Account
from groups.models import Group
from learnscripture.ftl_bundles import t, t_lazy


class EditGroupForm(forms.ModelForm):

    invited_users = forms.ModelMultipleChoiceField(
        label=t_lazy('groups-invited-users'),
        required=False,
        queryset=Account.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='account_autocomplete',
            attrs={
                'data-placeholder': t_lazy('accounts-username'),
                'data-minimum-input-length': 2,
            }),
    )

    class Meta:
        model = Group
        fields = ('name', 'description', 'public', 'open', 'invited_users')

    def clean_name(self):
        name = self.cleaned_data['name']
        name = name.strip()
        if name == '':
            raise forms.ValidationError(t('forms-field-required'))
        return name


f = EditGroupForm.base_fields['description'].widget.attrs
del f['cols']
f['rows'] = 3

EditGroupForm.base_fields['public'].help_text = t_lazy('groups-public-group-help-text')
EditGroupForm.base_fields['open'].help_text = t_lazy('groups-open-group-help-text')
