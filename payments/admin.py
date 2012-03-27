from django.contrib import admin

from .models import Price, Currency

class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol']

class PriceAdmin(admin.ModelAdmin):
    list_display = ['description', 'currency', 'amount', 'active']


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Price, PriceAdmin)

