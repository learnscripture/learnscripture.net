from django import forms
from django.utils.six import unichr
from mptt.forms import TreeNodeChoiceField

from cms.models import Page


class PageForm(forms.ModelForm):

    meta_description = forms.CharField(widget=forms.Textarea, required=False)
    meta_keywords = forms.CharField(widget=forms.Textarea, required=False)
    parent = TreeNodeChoiceField(queryset=Page.tree.all(), level_indicator=3 * unichr(160), empty_label='---------', required=False)
    redirect_page = TreeNodeChoiceField(label='Redirect page', queryset=Page.objects.filter(redirect_page__isnull=True), level_indicator=3 * unichr(160), empty_label='---------', required=False)

    class Meta:
        model = Page
        fields = '__all__'

    def clean_title(self):
        """
        Strips extra whitespace
        """
        return self.cleaned_data.get('title', '').strip()
