from django.contrib import admin

from .models import Price, Currency, Payment, Fund


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol']


class PriceAdmin(admin.ModelAdmin):
    list_display = ['description', 'currency', 'amount', 'active']


class FundAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'balance']
    filter_horizontal = ['members']
    readonly_fields = ['balance']

    def queryset(self, request):
        return super(FundAdmin, self).queryset(request).select_related('manager')


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'fund', 'amount', 'created']

    def queryset(self, request):
        return super(PaymentAdmin, self).queryset(request).select_related('account', 'fund')


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(Fund, FundAdmin)
admin.site.register(Payment, PaymentAdmin)
