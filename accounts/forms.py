from django.forms import ModelForm

from .models import Identity, Account


class PreferencesForm(ModelForm):
    class Meta:
        model = Identity
        fields = ['default_bible_version', 'enable_animations']


PreferencesForm.base_fields['default_bible_version'].required = True

