from django import forms
from django.forms import widgets
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from accounts.models import Account, SubscriptionType


class SignUpForm(forms.ModelForm):

    password = forms.CharField(max_length=100, widget=forms.PasswordInput)
    username = forms.RegexField(max_length=40,
                                regex=r'^[\w.+-]+$',
                                error_messages=
                                {'invalid': "This value may contain only letters, numbers and "
                                 "these characters: . + - _"})


    def clean_password(self):
        p = self.cleaned_data.get('password', '')
        if len(p) < settings.MINIMUM_PASSWORD_LENGTH:
            raise forms.ValidationError("The password must be at least %d characters" %
                                        settings.MINIMUM_PASSWORD_LENGTH)
        return p

    def clean_username(self):
        u = self.cleaned_data.get('username', '').strip()
        if Account.objects.filter(username__iexact=u).exists():
            raise forms.ValidationError("Account with this username already exists")
        return u

    def save(self, commit=True):
        """
        Saves the new password.
        """
        account = super(SignUpForm, self).save(commit=False)
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
            'is_under_13',
            ]

SignUpForm.base_fields['email'].help_text = "Private. Needed for notifications and password reset"
SignUpForm.base_fields['username'].help_text = "Public"
SignUpForm.base_fields['first_name'].help_text = "Optional, public"
SignUpForm.base_fields['last_name'].help_text = "Optional, public"


class LogInForm(forms.Form):
    email = forms.CharField(max_length=255, label="Email or username")
    password = forms.CharField(max_length=100, widget=forms.PasswordInput)

    def clean_password(self):
        def fail():
            raise forms.ValidationError(u"Can't find an account matching that username/email and password");
        try:
            email = self.cleaned_data.get('email', '').strip()
            if u'@' in email:
                accounts = Account.objects.filter(email__iexact=email)
                if len(accounts) == 0:
                    raise Account.DoesNotExist()
                elif len(accounts) > 1:
                    raise forms.ValidationError(u"Multiple accounts for this email address - please enter your username instead")
                else:
                    account = accounts[0]
            else:
                account = Account.objects.get(username__iexact=email)
        except Account.DoesNotExist:
            fail()

        p = self.cleaned_data.get('password', '')
        if not account.check_password(p):
            fail()
        return p


class AccountPasswordResetForm(PasswordResetForm):

    def clean_email(self):
        email = self.cleaned_data["email"]
        self.users_cache = Account.objects.filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        return email


class AccountSetPasswordForm(SetPasswordForm):
    pass


class ContactForm(forms.Form):
    name = forms.CharField(help_text=u"Optional", max_length=255, required=False)
    email = forms.EmailField(help_text=u"Optional", required=False)
    message = forms.CharField(max_length=10000, required=True, widget=widgets.Textarea)
