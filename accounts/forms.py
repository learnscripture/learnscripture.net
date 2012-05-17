from django import forms
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

from .models import Identity, Account, TestingMethod


class BootstrapRadioFieldRenderer(forms.RadioSelect.renderer):
    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        return mark_safe('<span id="id_%s"></span>' # We need this for AJAX validation error messages
                         '<ul class="inputs-list">\n%s\n</ul>'
                         % (self.name,
                            u'\n'.join([u'<li>%s</li>' % force_unicode(w) for w in self])))


class BootstrapRadioSelect(forms.RadioSelect):
    """
    RadioSelect with the inputs-list class, to match bootstrap style
    """
    renderer = BootstrapRadioFieldRenderer


class PreferencesForm(forms.ModelForm):
    testing_method = forms.ChoiceField(widget=BootstrapRadioSelect,
                                       choices=TestingMethod.choice_list,
                                       )

    def __init__(self, *args, **kwargs):
        super(PreferencesForm, self).__init__(*args, **kwargs)

        from bibleverses.models import BibleVersion
        available_bible_versions = BibleVersion.objects.filter(public=True)
        if 'instance' in kwargs:
            identity = kwargs['instance']
            if identity is not None:
                available_bible_versions = identity.available_bible_versions()

        self.fields['default_bible_version'].queryset = available_bible_versions

    class Meta:
        model = Identity
        fields = ['default_bible_version', 'testing_method',
                  'enable_animations', 'interface_theme']

PreferencesForm.base_fields['default_bible_version'].required = True


class AccountDetailsForm(forms.ModelForm):
    remind_after = forms.ChoiceField(choices=[(0, 'Never'),
                                              (1, 'after 1 day'),
                                              (2, 'after 2 days'),
                                              (3, 'after 3 days')],
                                     label="Send first reminder:"
                                     )

    remind_every = forms.ChoiceField(choices=[(0, 'Never'),
                                              (1, 'every day'),
                                              (2, 'every 2 days'),
                                              (3, 'every 3 days'),
                                              (7, 'every week')],
                                     label="Then remind:")

    class Meta:
        model = Account
        fields = ["first_name",
                  "last_name",
                  "email",
                  "is_under_13",
                  "remind_after",
                  "remind_every"]
