from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from .models import Identity, Account, SubscriptionType, Notice


def change_subscription_func(subscription_type, name, description):
    def change_subscription(modeladmin, request, queryset):
        queryset.update(subscription=subscription_type)
    change_subscription.short_description = description
    change_subscription.__name__ = name
    return change_subscription



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

class AccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name',
                    'subscription', 'date_joined', 'paid_until',
                    'payment_possible']
    readonly_fields = ['subscription', 'paid_until']
    actions = [
        change_subscription_func(SubscriptionType.FREE_TRIAL,
                                 "free_trial", "Change to free trial"),
        change_subscription_func(SubscriptionType.BASIC,
                                 "basic_account", "Change to basic account"),
        change_subscription_func(SubscriptionType.LIFETIME_FREE,
                                 "lifetime_free", "Change to lifetime free"),
        ]
    ordering = ['date_joined']
    search_fields = ['username', 'email']


class NoticeAdmin(admin.ModelAdmin):
    def queryset(self, request):
        return super(NoticeAdmin, self).queryset(request).select_related('for_identity', 'for_identity__account')


admin.site.register(Identity, IdentityAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Notice, NoticeAdmin)

