from django.contrib import admin

from .models import Identity, Account

admin.site.register(Identity)
admin.site.register(Account)

