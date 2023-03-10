from django import forms

from learnscripture.ftl_bundles import t_lazy

from .models import Account, Identity, TestingMethod


class PreferencesForm(forms.ModelForm):
    desktop_testing_method = forms.ChoiceField(
        label=t_lazy("accounts-testing-method"),
        widget=forms.RadioSelect,
        initial=TestingMethod.FIRST_LETTER,
        choices=TestingMethod.choices,
    )
    touchscreen_testing_method = forms.ChoiceField(
        label=t_lazy("accounts-testing-method"),
        widget=forms.RadioSelect,
        initial=TestingMethod.FIRST_LETTER,
        choices=TestingMethod.choices,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from bibleverses.models import TextVersion

        available_bible_versions = TextVersion.objects.bibles().visible_for_identity(kwargs.get("instance", None))
        self.fields["default_bible_version"].queryset = available_bible_versions

    class Meta:
        model = Identity
        fields = [
            "default_bible_version",
            "desktop_testing_method",
            "touchscreen_testing_method",
            "enable_sounds",
            "enable_vibration",
            "interface_theme",
        ]


PreferencesForm.base_fields["default_bible_version"].required = True


class AccountDetailsForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["first_name", "last_name", "email", "is_under_13"]

    def save(self, *args, **kwargs):
        if self.instance.id is not None:
            old_email = Account.objects.get(id=self.instance.id).email
        else:
            old_email = None

        super().save(*args, **kwargs)
        if old_email is not None and self.instance.email != old_email:
            self.instance.email_bounced = None
            self.instance.save()
