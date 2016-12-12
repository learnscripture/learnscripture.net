from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.core.urlresolvers import reverse
from django.utils.html import format_html

from .models import Account, Identity, Notice


class HasAccountListFilter(SimpleListFilter):
    title = "has account"
    parameter_name = 'has_account'

    def lookups(self, request, model_admin):
        return (
            ('1', 'No'),
            ('2', 'Yes'),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == '1':
            return queryset.filter(account__isnull=True)
        if val == '2':
            return queryset.filter(account__isnull=False)


class NoticeInline(admin.TabularInline):
    model = Notice
    raw_id_fields = ['related_event']
    extra = 1


class IdentityAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'date_created', 'default_bible_version',
                    'desktop_testing_method', 'interface_theme', 'referred_by']
    list_filter = [HasAccountListFilter, 'track_learning']
    inlines = [NoticeInline]

    def queryset(self, request):
        return super(IdentityAdmin, self).queryset(request).select_related('account', 'referred_by')


def hellban_account(modeladmin, request, queryset):
    queryset.update(is_hellbanned=True)
hellban_account.short_description = "Hell-ban selected accounts"  # noqa: E305


class IdentityInline(admin.StackedInline):
    model = Identity
    fk_name = 'account'


class HasBadEmailListFilter(SimpleListFilter):
    title = "has bad email address"
    parameter_name = "bad_email"

    def lookups(self, request, model_admin):
        return [
            ('0', 'No'),
            ('1', 'Yes'),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if val is None:
            return queryset
        return queryset.filter(email_bounced__isnull=True if self.value() == '0' else False)


class AccountAdmin(admin.ModelAdmin):
    def referred_by(account):
        return account.identity.referred_by

    def identity_link(account):
        return format_html('<a href="{0}">{1}</a>',
                           reverse('admin:accounts_identity_change', args=[account.identity.id]),
                           account.identity.id)
    list_display = ['username', identity_link, 'email', 'first_name', 'last_name', 'date_joined', 'email_bounced', 'is_hellbanned', referred_by]
    list_filter = [HasBadEmailListFilter,
                   'is_hellbanned',
                   'is_tester',
                   'is_moderator',
                   'is_under_13',
                   'enable_commenting',
                   ]
    ordering = ['date_joined']
    search_fields = ['username', 'email']
    filter_horizontal = ['following']
    actions = [hellban_account]
    inlines = [IdentityInline]

    def queryset(self, request):
        return super(AccountAdmin, self).queryset(request).select_related('identity__referred_by')


class NoticeAdmin(admin.ModelAdmin):
    def queryset(self, request):
        return super(NoticeAdmin, self).queryset(request).select_related('for_identity', 'for_identity__account')


admin.site.register(Identity, IdentityAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Notice, NoticeAdmin)
