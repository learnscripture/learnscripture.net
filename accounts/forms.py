from django import forms
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode

from .models import Identity, Account, TestingMethod


class BootstrapRadioFieldRenderer(forms.RadioSelect.renderer):
    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        return mark_safe(u'<ul class="inputs-list">\n%s\n</ul>' %
                         u'\n'.join([u'<li>%s</li>' % force_unicode(w) for w in self]))


class BootstrapRadioSelect(forms.RadioSelect):
    """
    RadioSelect with the inputs-list class, to match bootstrap style
    """
    renderer = BootstrapRadioFieldRenderer


class PreferencesForm(forms.ModelForm):
    testing_method = forms.ChoiceField(widget=BootstrapRadioSelect,
                                       choices=TestingMethod.choice_list,
                                       )
    class Meta:
        model = Identity
        fields = ['default_bible_version', 'testing_method',
                  'enable_animations', 'interface_theme']

PreferencesForm.base_fields['default_bible_version'].required = True
