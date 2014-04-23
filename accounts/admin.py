from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from .models import Identity, Account, Notice


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


class IdentityAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'date_created', 'default_bible_version',
                    'testing_method', 'interface_theme', 'referred_by']
    list_filter = (HasAccountListFilter,)

    def queryset(self, request):
        return super(IdentityAdmin, self).queryset(request).select_related('account', 'referred_by')


def hellban_account(modeladmin, request, queryset):
    queryset.update(is_hellbanned=True)
hellban_account.short_description = "Hell-ban selected accounts"


class AccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'date_joined', 'is_hellbanned']
    ordering = ['date_joined']
    search_fields = ['username', 'email']
    filter_horizontal = ['following']
    actions = [hellban_account]

class NoticeAdmin(admin.ModelAdmin):
    def queryset(self, request):
        return super(NoticeAdmin, self).queryset(request).select_related('for_identity', 'for_identity__account')


admin.site.register(Identity, IdentityAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Notice, NoticeAdmin)

