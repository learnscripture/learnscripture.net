from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
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
    active = models.BooleanField(default=False)
    message_html = models.TextField()
    hide_if_donated_days = models.PositiveIntegerField(
        help_text="The donation drive will be hidden for users who have donated within "
        "this number of days")
    target = models.DecimalField(default=Decimal("0"), decimal_places=0, max_digits=8)

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

    @cached_property
    def amount_raised(self):
        total = Payment.objects.filter(
            created__gt=self.start,
            created__lt=self.finish,
        ).aggregate(models.Sum('amount'))['amount__sum']
        if total is None:
            return Decimal('0')
        else:
            return total

    @property
    def fraction_raised(self):
        if self.target == 0:
            return 0
        else:
            return self.amount_raised / self.target

    @property
    def percentage_raised(self):
        return self.fraction_raised * 100

    def __unicode__(self):
        return "%s to %s" % (self.start.strftime("%Y-%m-%d"),
                             self.finish.strftime("%Y-%m-%d")
                             )

from payments import hooks
