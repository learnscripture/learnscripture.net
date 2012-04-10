from django.contrib import admin

from .models import Identity, Account, SubscriptionType


def change_subscription_func(subscription_type, name, description):
    def change_subscription(modeladmin, request, queryset):
        queryset.update(subscription=subscription_type)
    change_subscription.short_description = description
    change_subscription.__name__ = name
    return change_subscription


class AccountAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name',
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

admin.site.register(Identity)
admin.site.register(Account, AccountAdmin)

