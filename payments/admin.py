from django.contrib import admin

from .models import Payment, DonationDrive


class PaymentAdmin(admin.ModelAdmin):
    def email(obj):
        return obj.account.email

    list_display = ['id', 'account', email, 'amount', 'created']
    search_fields = ['account__username', 'account__email']

    def queryset(self, request):
        return super(PaymentAdmin, self).queryset(request).select_related('account')


class DonationDriveAdmin(admin.ModelAdmin):
    list_display = ['start', 'finish', 'active', 'hide_if_donated_days', 'target']
    list_filter = ['active']


admin.site.register(Payment, PaymentAdmin)
admin.site.register(DonationDrive, DonationDriveAdmin)
