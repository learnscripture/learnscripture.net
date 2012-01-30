from django import forms
from django.conf import settings

from accounts.models import Account, SubscriptionType


class SignupForm(forms.ModelForm):

    password = forms.CharField(max_length=100, widget=forms.PasswordInput)

    def clean_password(self):
        p = self.cleaned_data.get('password', '')
        if len(p) < settings.MINIMUM_PASSWORD_LENGTH:
            raise forms.ValidationError("The password must be at least %d characters" %
                                        settings.MINIMUM_PASSWORD_LENGTH)
        return p

    def save(self, commit=True):
        """
        Saves the new password.
        """
        account = super(SignupForm, self).save(commit=False)
        account.set_password(self.cleaned_data["password"])
        account.subscription = SubscriptionType.FREE_TRIAL

        if commit:
            account.save()
        return account

    class Meta:
        model = Account
        fields = [
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            ]


