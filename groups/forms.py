from dal import autocomplete
from django import forms

from accounts.models import Account
from groups.models import Group
from learnscripture.ftl_bundles import t, t_lazy


class MyModelSelect2Multiple(autocomplete.ModelSelect2Multiple):
    @property
    def media(self):
        retval = super().media
        jquery_dep = "admin/js/vendor/jquery/jquery.js"
        # ModelSelect2Multiple assumes we are in admin, which has already
        # loaded jQuery.
        if not any(jquery_dep in jslist for jslist in retval._js_lists):
            # Insert it at the beginning
            retval._js_lists = [(jquery_dep,)] + retval._js_lists
        return retval


class EditGroupForm(forms.ModelForm):

    invited_users = forms.ModelMultipleChoiceField(
        label=t_lazy("groups-invited-users"),
        required=False,
        queryset=Account.objects.all(),
        widget=MyModelSelect2Multiple(
            url="account_autocomplete",
            attrs={
                "data-placeholder": t_lazy("accounts-username"),
                "data-minimum-input-length": 2,
            },
        ),
    )

    class Meta:
        model = Group
        fields = ["name", "description", "language_code", "public", "open", "invited_users"]

    def clean_name(self):
        name = self.cleaned_data["name"]
        name = name.strip()
        if name == "":
            raise forms.ValidationError(t("forms-field-required"))
        return name


f = EditGroupForm.base_fields["description"].widget.attrs
del f["cols"]
f["rows"] = 3

EditGroupForm.base_fields["public"].help_text = t_lazy("groups-public-group-help-text")
EditGroupForm.base_fields["open"].help_text = t_lazy("groups-open-group-help-text")
