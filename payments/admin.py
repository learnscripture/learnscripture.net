from django.contrib import admin

from .models import Price, Currency, Payment


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol']


class PriceAdmin(admin.ModelAdmin):
    list_display = ['description', 'currency', 'amount', 'active']


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'amount', 'created']

    def queryset(self, request):
        return super(PaymentAdmin, self).queryset(request).select_related('account')


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(Payment, PaymentAdmin)
