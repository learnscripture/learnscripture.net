from django.db import models
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN

from accounts.models import Account


class PaymentManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return super(PaymentManager, self).get_query_set().select_related('account')


class Payment(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    account = models.ForeignKey(Account, related_name='payments')
    paypal_ipn = models.ForeignKey(PayPalIPN)
    created = models.DateTimeField()

    objects = PaymentManager()

    def __unicode__(self):
        return u"Payment: %s from %s" % (self.amount, self.account)


class DonationDriveManager(models.Manager):
    def current(self):
        now = timezone.now()
        return self.filter(start__lte=now,
                           finish__gte=now,
                           active=True)

    def current_for_account(self, account):
        if account.donations_disabled():
            return []
        return [
            d for d in self.current()
            if d.active_for_account(account)
            ]


class DonationDrive(models.Model):
    start = models.DateTimeField()
    finish = models.DateTimeField()
    active = models.BooleanField()
    message_html = models.TextField()
    hide_if_donated_days = models.PositiveIntegerField(
        help_text="The donation drive will be hidden for users who have donated within "
        "this number of days")

    objects = DonationDriveManager()

    def active_for_account(self, account):
        # We do this within a method on DonationDrive, rather than as part of
        # the DonationDriveManager.current query, because it requires additional
        # DB queries, and in general it will be faster to do a single query and
        # discover that there are no current DonationDrives, than do the queries
        # required to get last payment.
        if account.donations_disabled():
            return False
        try:
            last_payment = account.payments.order_by('-created')[0]
        except IndexError:
            # No payments:
            return True
        now = timezone.now()
        return (now - last_payment.created).days > self.hide_if_donated_days

    def __unicode__(self):
        return "%s to %s" % (self.start.strftime("%Y-%m-%d"),
                             self.finish.strftime("%Y-%m-%d")
                             )

import payments.hooks
