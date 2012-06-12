from django import forms
import selectable.forms.fields

from payments.models import Fund
from accounts.lookups import AccountLookup


class EditFundForm(forms.ModelForm):

    members = selectable.forms.fields.AutoCompleteSelectMultipleField(
        lookup_class=AccountLookup,
        label=u'Members',
        required=False
        )

    class Meta:
        model = Fund
        fields = ('name', 'currency', 'members')

    def clean_name(self):
        name = self.cleaned_data['name']
        name = name.strip()
        if name == '':
            raise forms.ValidationError("This field is required")
        return name

    def save(self, **kwargs):
        if self.instance.id is not None:
            # can't change currency after creating.
            self.instance.currency = Fund.objects.get(id=self.instance.id).currency
        return super(EditFundForm, self).save(**kwargs)
