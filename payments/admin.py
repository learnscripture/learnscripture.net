from django.contrib import admin

from .models import DonationDrive, Payment


class PaymentAdmin(admin.ModelAdmin):
    def email(obj):
        return obj.account.email

    list_display = ['id', 'account', email, 'amount', 'created']
    search_fields = ['account__username', 'account__email']

    def get_queryset(self, request):
        return super(PaymentAdmin, self).get_queryset(request).select_related('account')


class DonationDriveAdmin(admin.ModelAdmin):
    list_display = ['start', 'finish', 'active', 'hide_if_donated_days', 'target', 'language_code']
    list_filter = ['active', 'language_code']


admin.site.register(Payment, PaymentAdmin)
admin.site.register(DonationDrive, DonationDriveAdmin)
