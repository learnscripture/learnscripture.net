from dal import autocomplete
from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.urls import reverse

from common.utils.html import link
from moderation import models as moderation

from .models import Account, Identity, Notice

account_autocomplete_widget = lambda: autocomplete.ModelSelect2(url="account_autocomplete")
multi_account_autocomplete_widget = lambda: autocomplete.ModelSelect2Multiple(url="account_autocomplete")


class HasAccountListFilter(SimpleListFilter):
    title = "has account"
    parameter_name = "has_account"

    def lookups(self, request, model_admin):
        return (
            ("1", "No"),
            ("2", "Yes"),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == "1":
            return queryset.filter(account__isnull=True)
        if val == "2":
            return queryset.filter(account__isnull=False)


class NoticeInline(admin.TabularInline):
    model = Notice
    raw_id_fields = ["related_event"]
    extra = 1


class IdentityForm(forms.ModelForm):
    class Meta:
        model = Identity
        fields = "__all__"
        widgets = {
            "account": account_autocomplete_widget(),
            "referred_by": account_autocomplete_widget(),
        }


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    form = IdentityForm
    list_display = [
        "id",
        "account",
        "date_created",
        "default_bible_version",
        "desktop_testing_method",
        "interface_theme",
        "referred_by",
    ]
    list_filter = [HasAccountListFilter]
    search_fields = ["account__username"]
    inlines = [NoticeInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("account", "referred_by")


@admin.action(description="Shadow-ban selected accounts")
def hellban_account(modeladmin, request, queryset):
    for user in queryset:
        moderation.hellban_user(user, by=request.user, duration=None)


@admin.action(description="Make selected accounts into testers")
def make_tester(ModelAdmin, request, queryset):
    queryset.update(is_tester=True)


@admin.action(description="Make selected accounts into non-testers")
def unmake_tester(ModelAdmin, request, queryset):
    queryset.update(is_tester=False)


class IdentityInline(admin.StackedInline):
    model = Identity
    form = IdentityForm
    fk_name = "account"


class HasBadEmailListFilter(SimpleListFilter):
    title = "has bad email address"
    parameter_name = "bad_email"

    def lookups(self, request, model_admin):
        return [
            ("0", "No"),
            ("1", "Yes"),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if val is None:
            return queryset
        return queryset.filter(email_bounced__isnull=True if self.value() == "0" else False)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = "__all__"
        widgets = {
            "following": multi_account_autocomplete_widget(),
        }


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    form = AccountForm

    def referred_by(account):
        return account.identity.referred_by

    def identity_link(account):
        return link(reverse("admin:accounts_identity_change", args=[account.identity.id]), account.identity.id)

    list_display = [
        "username",
        identity_link,
        "email",
        "first_name",
        "last_name",
        "date_joined",
        "email_bounced",
        "is_hellbanned",
        referred_by,
    ]
    list_filter = [
        HasBadEmailListFilter,
        "is_hellbanned",
        "is_tester",
        "is_moderator",
        "is_under_13",
        "enable_commenting",
    ]
    ordering = ["date_joined"]
    search_fields = ["username", "email"]
    actions = [
        hellban_account,
        make_tester,
        unmake_tester,
    ]
    inlines = [IdentityInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("identity__referred_by")


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    raw_id_fields = ["for_identity", "related_event"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("for_identity", "for_identity__account")
