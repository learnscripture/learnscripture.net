from django.db import models
from paypal.standard.ipn.models import PayPalIPN

from accounts.models import Account


class PaymentManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return super(PaymentManager, self).get_query_set().select_related('account')


class Payment(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    account = models.ForeignKey(Account, null=True, blank=True, related_name='payments')
    paypal_ipn = models.ForeignKey(PayPalIPN)
    created = models.DateTimeField()

    objects = PaymentManager()

    def __unicode__(self):
        return u"Payment: %s to %s" % (self.amount, self.account if self.account else u"fund '%s'" % self.fund)


class DonationDrive(models.Model):
    start = models.DateTimeField()
    finish = models.DateTimeField()
    active = models.BooleanField()
    message_html = models.TextField()
    hide_if_donated_days = models.PositiveIntegerField(
        help_text="The donation drive will be hidden for users who have donated within "
        "this number of days")

import payments.hooks
