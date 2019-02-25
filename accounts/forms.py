from django import forms

from learnscripture.ftl_bundles import t_lazy

from .models import Account, Identity, TestingMethod


class PreferencesForm(forms.ModelForm):
    desktop_testing_method = forms.ChoiceField(label=t_lazy('accounts-testing-method'),
                                               widget=forms.RadioSelect,
                                               initial=TestingMethod.FULL_WORDS,
                                               choices=TestingMethod.choice_list)
    touchscreen_testing_method = forms.ChoiceField(label=t_lazy('accounts-testing-method'),
                                                   widget=forms.RadioSelect,
                                                   initial=TestingMethod.ON_SCREEN,
                                                   choices=TestingMethod.choice_list)

    def __init__(self, *args, **kwargs):
        super(PreferencesForm, self).__init__(*args, **kwargs)

        from bibleverses.models import TextVersion
        available_bible_versions = TextVersion.objects.bibles().filter(public=True)
        if 'instance' in kwargs:
            identity = kwargs['instance']
        else:
            identity = None

        if identity is not None:
            available_bible_versions = identity.available_bible_versions()

        if identity is None or not identity.i18n_options_enabled:
            del self.fields['interface_language']

        self.fields['default_bible_version'].queryset = available_bible_versions

    class Meta:
        model = Identity
        fields = ['default_bible_version',
                  'desktop_testing_method',
                  'touchscreen_testing_method',
                  'enable_sounds',
                  'enable_vibration',
                  'interface_theme',
                  'interface_language',
                  ]


PreferencesForm.base_fields['default_bible_version'].required = True


class AccountDetailsForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ["first_name",
                  "last_name",
                  "email",
                  "is_under_13"]

    def save(self, *args, **kwargs):
        if self.instance.id is not None:
            old_email = Account.objects.get(id=self.instance.id).email
        else:
            old_email = None

        super(AccountDetailsForm, self).save(*args, **kwargs)
        if old_email is not None and self.instance.email != old_email:
            self.instance.email_bounced = None
            self.instance.save()
