from django.contrib import admin

from .models import Identity, Account

class AccountAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name',
                    'subscription', 'date_joined', 'paid_until',
                    'payment_possible']
    readonly_fields = ['subscription', 'paid_until']

admin.site.register(Identity)
admin.site.register(Account, AccountAdmin)

