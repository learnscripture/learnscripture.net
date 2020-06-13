from decimal import Decimal

from django.conf import settings
from django.core import mail
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django_ftl import override
from fluent_compiler import types as fluent_types
from paypal.standard.ipn.models import PayPalIPN

from accounts.models import Account
from learnscripture.ftl_bundles import t


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

    def __str__(self):
        return f"Payment: {self.amount} from {self.account}"


class DonationDriveManager(models.Manager):
    def current(self, language_code):
        now = timezone.now()
        return [d for d in self.filter(start__lte=now,
                                       finish__gte=now,
                                       language_code=language_code,
                                       active=True)
                if not d.target_reached]

    def current_for_account(self, account):
        if account.donations_disabled():
            return []
        return [
            d for d in self.current(account.default_language_code)
            if d.active_for_account(account)
        ]


class DonationDrive(models.Model):
    start = models.DateTimeField()
    finish = models.DateTimeField()
    active = models.BooleanField(default=False)
    message_html = models.TextField()
    language_code = models.CharField(max_length=10,
                                     choices=settings.LANGUAGES,
                                     default=settings.LANGUAGE_CODE)
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
        if self.language_code != account.default_language_code:
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

    @cached_property
    def amount_raised_formatted(self):
        return fluent_types.fluent_number(self.amount_raised,
                                          style=fluent_types.FORMAT_STYLE_CURRENCY,
                                          currencyDisplay=fluent_types.CURRENCY_DISPLAY_SYMBOL,
                                          currency="GBP")

    @cached_property
    def target_formatted(self):
        return fluent_types.fluent_number(self.target,
                                          style=fluent_types.FORMAT_STYLE_CURRENCY,
                                          currencyDisplay=fluent_types.CURRENCY_DISPLAY_SYMBOL,
                                          currency="GBP")

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

    def __str__(self):
        return "%s to %s" % (self.start.strftime("%Y-%m-%d"),
                             self.finish.strftime("%Y-%m-%d")
                             )


def send_donation_drive_target_reached_emails(donation_drive):
    from django.conf import settings
    from learnscripture.utils.templates import render_to_string_ftl

    payments = donation_drive.get_contributions()
    recipient_data = [{
        'language_code': payment.account.default_language_code,
        'name': payment.account.email_name,
        'email': payment.account.email,
        'amount': fluent_types.fluent_number(payment.amount,
                                             style=fluent_types.FORMAT_STYLE_CURRENCY,
                                             currencyDisplay=fluent_types.CURRENCY_DISPLAY_SYMBOL,
                                             currency="GBP")
    }
        for payment in payments
    ]

    # Add one to the admins:
    for name, email in settings.ADMINS:
        recipient_data.append({
            'language_code': 'en',
            'name': name or "Admin",
            'email': email,
            'amount': 0,
        })
    c_base = {
        'target': donation_drive.target_formatted
    }
    for d in recipient_data:
        context = c_base.copy()
        context.update(d)
        with override(d['language_code']):
            body = render_to_string_ftl("learnscripture/donation_drive_target_reached_email.txt", context)
            subject = t('donations-target-reached-email-subject')
        mail.send_mail(subject, body, settings.SERVER_EMAIL, [d['email']])
