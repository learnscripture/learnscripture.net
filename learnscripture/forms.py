from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.forms import widgets
from django.urls import reverse

from accounts.models import Account
from bibleverses.models import TextType, VerseSetType
from learnscripture.ftl_bundles import t, t_lazy


class FilterFormMixin(object):
    """
    Mixin for forms that act as filters.

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

    password = forms.CharField(label=t_lazy('accounts-password'),
                               max_length=100,
                               widget=forms.PasswordInput)
    username = forms.RegexField(label=t_lazy('accounts-username'),
                                max_length=40,
                                regex=r'^[\w.+-]+$',
                                error_messages={'invalid':
                                                t_lazy('accounts-username-validation')})

    def clean_password(self):
        p = self.cleaned_data.get('password', '')
        if len(p) < settings.MINIMUM_PASSWORD_LENGTH:
            raise forms.ValidationError(t('accounts-password-length-validation',
                                          dict(length=settings.MINIMUM_PASSWORD_LENGTH)))
        return p

    def clean_username(self):
        u = self.cleaned_data.get('username', '').strip()
        if Account.objects.filter(username__iexact=u).exists():
            raise forms.ValidationError(t('accounts-username-already-taken'))
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


SignUpForm.base_fields['email'].help_text = t_lazy('accounts-email-help-text')
SignUpForm.base_fields['username'].help_text = t_lazy('forms-field-public')
SignUpForm.base_fields['first_name'].help_text = t_lazy('forms-field-optional')
SignUpForm.base_fields['last_name'].help_text = t_lazy('forms-field-public-optional')


class LogInForm(forms.Form):
    email = forms.CharField(label=t_lazy('accounts-login-email-or-username'),
                            max_length=255)
    password = forms.CharField(label=t_lazy('accounts-password'),
                               max_length=100,
                               required=False,
                               widget=forms.PasswordInput)

    def clean(self):
        def fail():
            raise forms.ValidationError(t('accounts-login-no-matching-username-password'))
        try:
            email = self.cleaned_data.get('email', '').strip()
            if '@' in email:
                accounts = Account.objects.active().filter(email__iexact=email)
                if len(accounts) == 0:
                    raise Account.DoesNotExist()
                elif len(accounts) > 1:
                    raise forms.ValidationError(t('accounts-login-multiple-accounts'))
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
    # Override fields so we can set label correctly
    email = forms.EmailField(label=t_lazy('accounts-email'), max_length=254)

    error_messages = {
        'unknown': t_lazy('accounts-reset-email-not-found'),
        'password_mismatch': t_lazy('accounts-password-mismatch'),
    }

    def clean_email(self):
        email = self.cleaned_data["email"]
        self.users_cache = Account.objects.active().filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        return email

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        # We add 'reset_url' to context, which is easier to do in Python than in
        # the template.
        path = reverse('password_reset_confirm', kwargs={'uidb64': context['uid'],
                                                         'token': context['token']})
        context['reset_url'] = "{protocol}://{domain}{path}".format(path=path, **context)
        return super().send_mail(subject_template_name, email_template_name,
                                 context, from_email, to_email, html_email_template_name=html_email_template_name)


class AccountSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=t_lazy('accounts-new-password'),
        widget=forms.PasswordInput,
        strip=False,
    )
    new_password2 = forms.CharField(
        label=t_lazy('accounts-new-password-confirmation'),
        strip=False,
        widget=forms.PasswordInput,
    )


class AccountPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label=t_lazy('accounts-old-password'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autofocus': True}),
    )
    new_password1 = forms.CharField(
        label=t_lazy('accounts-new-password'),
        widget=forms.PasswordInput,
        strip=False,
    )
    new_password2 = forms.CharField(
        label=t_lazy('accounts-new-password-confirmation'),
        strip=False,
        widget=forms.PasswordInput,
    )

    error_messages = dict(AccountSetPasswordForm.error_messages, **{
        'password_incorrect': t_lazy('accounts-old-password-incorrect'),
    })


class ContactForm(forms.Form):
    name = forms.CharField(
        label=t_lazy('contact-form-name'),
        help_text=t_lazy('forms-field-optional'), max_length=255, required=False)
    email = forms.EmailField(
        label=t_lazy('contact-form-email'),
        help_text=t_lazy('forms-field-optional'), required=False)
    message = forms.CharField(
        max_length=10000, required=True,
        help_text=t_lazy('contact-form-message-help-text'),
        widget=widgets.Textarea(attrs={'rows': '10'}))


VERSE_SET_ORDER_POPULARITY = "popularity"
VERSE_SET_ORDER_AGE = "age"

VERSE_SET_TYPE_ALL = "all"
VERSE_SET_TYPE_CHOICES = [
    (VERSE_SET_TYPE_ALL, t_lazy('versesets-filter-all')),
    (VerseSetType.SELECTION, t_lazy('versesets-filter-selection-caption')),
    (VerseSetType.PASSAGE, t_lazy('versesets-filter-passage-caption')),
]


class VerseSetSearchForm(FilterFormMixin, forms.Form):
    query = forms.CharField(label=t_lazy('versesets-search'), required=False)
    set_type = forms.ChoiceField(choices=VERSE_SET_TYPE_CHOICES,
                                 initial=VERSE_SET_TYPE_ALL,
                                 label=t_lazy('versesets-filter-type'),
                                 required=False,
                                 widget=widgets.RadioSelect
                                 )
    order = forms.ChoiceField(choices=[(VERSE_SET_ORDER_POPULARITY, t_lazy('versesets-order-most-popular-first')),
                                       (VERSE_SET_ORDER_AGE, t_lazy('versesets-order-newest-first')),
                                       ],
                              initial=VERSE_SET_ORDER_POPULARITY,
                              label=t_lazy('versesets-order'),
                              required=False,
                              widget=widgets.RadioSelect
                              )


LEADERBOARD_WHEN_ALL_TIME = 'alltime'
LEADERBOARD_WHEN_THIS_WEEK = 'thisweek'


class LeaderboardFilterForm(FilterFormMixin, forms.Form):
    when = forms.ChoiceField(choices=[(LEADERBOARD_WHEN_ALL_TIME, t_lazy('leaderboards-filter-all-time')),
                                      (LEADERBOARD_WHEN_THIS_WEEK, t_lazy('leaderboards-filter-this-week')),
                                      ],
                             initial=LEADERBOARD_WHEN_ALL_TIME,
                             label=t_lazy('leaderboards-filter-when'),
                             required=False,
                             widget=widgets.RadioSelect)


GROUP_WALL_ORDER_NEWEST_FIRST = 'newestfirst'
GROUP_WALL_ORDER_OLDEST_FIRST = 'oldestfirst'


class GroupWallFilterForm(FilterFormMixin, forms.Form):
    order = forms.ChoiceField(choices=[(GROUP_WALL_ORDER_NEWEST_FIRST, t_lazy('groups-messages-order-most-recent-first')),
                                       (GROUP_WALL_ORDER_OLDEST_FIRST, t_lazy('groups-messages-order-oldest-first'))],
                              initial=GROUP_WALL_ORDER_NEWEST_FIRST,
                              label=t_lazy('groups-messages-order'),
                              required=False,
                              widget=widgets.RadioSelect)


class GroupFilterForm(FilterFormMixin, forms.Form):
    query = forms.CharField(label=t_lazy('groups-search'), required=False)


USER_VERSES_ORDER_WEAKEST = "weakestfirst"
USER_VERSES_ORDER_STRONGEST = "strongestfirst"
USER_VERSES_ORDER_TEXT_ORDER = "textorder"


class UserVersesFilterForm(FilterFormMixin, forms.Form):
    query = forms.CharField(label=t_lazy('user-verses-filter-query'), required=False,
                            widget=forms.TextInput(attrs={'placeholder': t_lazy('user-verses-filter-query.placeholder')}))
    text_type = forms.ChoiceField(choices=TextType.choice_list,
                                  initial=TextType.BIBLE,
                                  label=t_lazy('user-verses-filter-type'),
                                  required=False,
                                  widget=widgets.RadioSelect)
    order = forms.ChoiceField(choices=[(USER_VERSES_ORDER_WEAKEST, t_lazy('user-verses-order-weakest-first')),
                                       (USER_VERSES_ORDER_STRONGEST, t_lazy('user-verses-order-strongest-first')),
                                       (USER_VERSES_ORDER_TEXT_ORDER, t_lazy('user-verses-order-text'))],
                              initial=USER_VERSES_ORDER_WEAKEST,
                              label=t_lazy('user-verses-order'),
                              required=False,
                              widget=widgets.RadioSelect)
