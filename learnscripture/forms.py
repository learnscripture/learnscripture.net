from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.forms import widgets

from accounts.models import Account
from bibleverses.models import VerseSetType


class FilterFormMixin(object):
    """
    Mixing for forms that act as filters.

    These forms should always be valid, including in initial state, and any
    state that can be set using the UI - they never show error messages.
    """
    @classmethod
    def from_request_data(cls, request_data):
        data = {}
        initial_data = {}
        for name, f in cls.base_fields.items():
            initial_data[name] = f.initial
            if name in request_data:
                data[name] = request_data[name]
            else:
                data[name] = initial_data[name]

        # First check on a different instance.
        checker_instance = cls(data=data)
        # Removed anything that doesn't validate
        if not checker_instance.is_valid():
            for k in checker_instance.errors.as_data().keys():
                data[name] = initial_data[name]

        instance = cls(data=data)
        # Immediately run is_valid, so that we can use cleaned_data
        if not instance.is_valid():
            raise AssertionError("{0} should always be valid: {1}"
                                 .format(cls,
                                         instance.errors.as_data()))
        return instance


class SignUpForm(forms.ModelForm):

    password = forms.CharField(max_length=100, widget=forms.PasswordInput)
    username = forms.RegexField(max_length=40,
                                regex=r'^[\w.+-]+$',
                                error_messages={'invalid':
                                                "This value may contain only letters, numbers and "
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
            'enable_commenting',
        ]


SignUpForm.base_fields['email'].help_text = "Private. Needed for notifications and password reset"
SignUpForm.base_fields['username'].help_text = "Public"
SignUpForm.base_fields['first_name'].help_text = "Optional, public"
SignUpForm.base_fields['last_name'].help_text = "Optional, public"


class LogInForm(forms.Form):
    email = forms.CharField(max_length=255, label="Email or username")
    password = forms.CharField(max_length=100,
                               required=False,
                               widget=forms.PasswordInput)

    def clean(self):
        def fail():
            raise forms.ValidationError("Can't find an account matching that username/email and password")
        try:
            email = self.cleaned_data.get('email', '').strip()
            if '@' in email:
                accounts = Account.objects.active().filter(email__iexact=email)
                if len(accounts) == 0:
                    raise Account.DoesNotExist()
                elif len(accounts) > 1:
                    raise forms.ValidationError("Multiple accounts for this email address - please enter your username instead")
                else:
                    account = accounts[0]
            else:
                account = Account.objects.get(username__iexact=email)
        except Account.DoesNotExist:
            fail()

        if not account.check_password(self.cleaned_data.get('password', '')):
            fail()

        self.cleaned_data['account'] = account
        return self.cleaned_data


class AccountPasswordResetForm(PasswordResetForm):

    error_messages = {
        'unknown': "That email address doesn't have an associated user account. Are you sure you've registered?",
    }

    def clean_email(self):
        email = self.cleaned_data["email"]
        self.users_cache = Account.objects.active().filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        return email


class AccountSetPasswordForm(SetPasswordForm):
    pass


class AccountPasswordChangeForm(PasswordChangeForm):
    pass


class ContactForm(forms.Form):
    name = forms.CharField(help_text="Optional", max_length=255, required=False)
    email = forms.EmailField(help_text="Optional", required=False)
    message = forms.CharField(max_length=10000, required=True,
                              help_text="If you are reporting a problem, please include a full and specific description, "
                              "and include what device/browser you are using, with version numbers.",
                              widget=widgets.Textarea(attrs={'rows': '10'}))


VERSE_SET_ORDER_POPULARITY = "popularity"
VERSE_SET_ORDER_AGE = "age"

VERSE_SET_TYPE_ALL = "all"
VERSE_SET_TYPE_CHOICES = [
    (VERSE_SET_TYPE_ALL, "All"),
    (VerseSetType.SELECTION, "Selection - hand-picked verses usually on a theme or topic"),
    (VerseSetType.PASSAGE, "Passage - continuous verses in a chapter"),
]


class VerseSetSearchForm(FilterFormMixin, forms.Form):
    query = forms.CharField(label="Search", required=False)
    set_type = forms.ChoiceField(choices=VERSE_SET_TYPE_CHOICES,
                                 initial=VERSE_SET_TYPE_ALL,
                                 label="Type",
                                 required=False,
                                 widget=widgets.RadioSelect
                                 )
    order = forms.ChoiceField(choices=[(VERSE_SET_ORDER_POPULARITY, "Most popular first"),
                                       (VERSE_SET_ORDER_AGE, "Newest first"),
                                       ],
                              initial=VERSE_SET_ORDER_POPULARITY,
                              label="Order",
                              required=False,
                              widget=widgets.RadioSelect
                              )


LEADERBOARD_WHEN_ALL_TIME = 'alltime'
LEADERBOARD_WHEN_THIS_WEEK = 'thisweek'


class LeaderboardFilterForm(FilterFormMixin, forms.Form):
    when = forms.ChoiceField(choices=[(LEADERBOARD_WHEN_ALL_TIME, "All time"),
                                      (LEADERBOARD_WHEN_THIS_WEEK, "This week"),
                                      ],
                             initial=LEADERBOARD_WHEN_ALL_TIME,
                             label="When",
                             required=False,
                             widget=widgets.RadioSelect)


GROUP_WALL_ORDER_NEWEST_FIRST = 'newestfirst'
GROUP_WALL_ORDER_OLDEST_FIRST = 'oldestfirst'


class GroupWallFilterForm(FilterFormMixin, forms.Form):
    order = forms.ChoiceField(choices=[(GROUP_WALL_ORDER_NEWEST_FIRST, "Most recent first"),
                                       (GROUP_WALL_ORDER_OLDEST_FIRST, "Oldest first")],
                              initial=GROUP_WALL_ORDER_NEWEST_FIRST,
                              label="Order",
                              required=False,
                              widget=widgets.RadioSelect)
