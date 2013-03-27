from django.contrib import admin

from .models import Payment, DonationDrive

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'amount', 'created']

    def queryset(self, request):
        return super(PaymentAdmin, self).queryset(request).select_related('account')


admin.site.register(Payment, PaymentAdmin)
admin.site.register(DonationDrive)
