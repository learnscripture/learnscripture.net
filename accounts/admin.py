from django.contrib import admin

from .models import Identity, Account

class AccountAdmin(admin.ModelAdmin):
    readonly_fields = ['subscription', 'paid_until']

admin.site.register(Identity)
admin.site.register(Account, AccountAdmin)

