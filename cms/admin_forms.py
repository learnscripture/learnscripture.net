from django import forms
from mptt.forms import TreeNodeChoiceField

from cms.models import Page, PageTitle


class PageForm(forms.ModelForm):
    parent = TreeNodeChoiceField(
        queryset=Page.tree.all(), level_indicator=3 * chr(160), empty_label="---------", required=False
    )
    redirect_page = TreeNodeChoiceField(
        label="Redirect page",
        queryset=Page.objects.filter(redirect_page__isnull=True),
        level_indicator=3 * chr(160),
        empty_label="---------",
        required=False,
    )

    class Meta:
        model = Page
        fields = "__all__"


class PageTitleForm(forms.ModelForm):
    class Meta:
        model = PageTitle
        fields = "__all__"

    def clean_title(self):
        """
        Strips extra whitespace
        """
        return self.cleaned_data.get("title", "").strip()
