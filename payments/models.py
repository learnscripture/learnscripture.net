from __future__ import unicode_literals

from decimal import Decimal

from django.conf import settings
from django.core import mail
from django.db import models
from django.template import loader
from django.utils import timezone
from django.utils.functional import cached_property
from paypal.standard.ipn.models import PayPalIPN

from accounts.models import Account


class PaymentManager(models.Manager):

    def get_queryset(self):
        return super(PaymentManager, self).get_queryset().select_related('account')


class Payment(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    account = models.ForeignKey(Account, on_delete=models.CASCADE,
                                related_name='payments')
    paypal_ipn = models.ForeignKey(PayPalIPN, on_delete=models.CASCADE,
                                   related_name='payments')
    created = models.DateTimeField()

    objects = PaymentManager()

    class Meta:
        base_manager_name = 'objects'

    def __unicode__(self):
        return u"Payment: %s from %s" % (self.amount, self.account)


class DonationDriveManager(models.Manager):
    def current(self):
        now = timezone.now()
        return [d for d in self.filter(start__lte=now,
                                       finish__gte=now,
                                       active=True)
                if not d.target_reached]

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
        return self.get_amount_raised()

    def get_amount_raised(self, before=None):
        # if before is not None, it is used to limit the query further.

        # Use PayPalIPN instead of Payment, so that we include donations that
        # are not assigned to account for whatever reason.

        # This means we need to handle non-GBP payments as well.

        initial_qs = PayPalIPN.objects.all()
        if before is not None:
            initial_qs = initial_qs.filter(created_at__lt=before)

        total1 = initial_qs.filter(
            created_at__gt=self.start,
            created_at__lt=self.finish,
            mc_currency=settings.VALID_RECEIVE_CURRENCY
        ).aggregate(models.Sum('mc_gross'))['mc_gross__sum']
        if total1 is None:
            total1 = Decimal('0')

        total2 = initial_qs.filter(
            created_at__gt=self.start,
            created_at__lt=self.finish,
            settle_currency=settings.VALID_RECEIVE_CURRENCY
        ).aggregate(models.Sum('settle_amount'))['settle_amount__sum']
        if total2 is None:
            total2 = Decimal('0')

        return total1 + total2

    def get_contributions(self):
        return Payment.objects.filter(
            created__gt=self.start,
            created__lt=self.finish)

    @property
    def fraction_raised(self):
        if self.target == 0:
            return 0
        else:
            return self.amount_raised / self.target

    @property
    def percentage_raised(self):
        return self.fraction_raised * 100

    @property
    def target_reached(self):
        return self.fraction_raised >= 1  # Always false if target==0

    def __unicode__(self):
        return "%s to %s" % (self.start.strftime("%Y-%m-%d"),
                             self.finish.strftime("%Y-%m-%d")
                             )


def send_donation_drive_target_reached_emails(donation_drive):
    from django.conf import settings

    payments = donation_drive.get_contributions()
    recipient_data = [{
        'name': payment.account.email_name,
        'email': payment.account.email,
        'amount': payment.amount}
        for payment in payments
    ]

    # Add one to the admins:
    for name, email in settings.ADMINS:
        recipient_data.append({
            'name': name or "Admin",
            'email': email,
            'amount': None,
        })
    c_base = {
        'donation_drive': donation_drive,
        'other_contributors': len(payments) - 1,
    }
    for d in recipient_data:
        context = c_base.copy()
        context.update(d)
        body = loader.render_to_string("learnscripture/donation_drive_target_reached_email.txt", context)
        subject = "LearnScripture.net - donation target reached!"
        mail.send_mail(subject, body, settings.SERVER_EMAIL, [d['email']])


from payments import hooks  # NOQA isort:skip
