from decimal import Decimal

from django.db import models
from django.utils import timezone
from paypal.standard.ipn.models import PayPalIPN

from accounts.models import Account


class CurrencyManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get_query_set().get(name=name)


class Currency(models.Model):
    name = models.CharField(max_length=10, unique=True)
    symbol = models.CharField(max_length=10)

    objects = CurrencyManager()

    def __repr__(self):
        return u"<Currency %s>" % self.name

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name,)

    class Meta:
        verbose_name_plural = 'Currencies'


class PriceManager(models.Manager):
    def current_prices(self):
        """
        Get a list of prices, as a list of (currency, [list of Price objects]) tuples
        """
        qs = self.get_query_set().filter(active=True).order_by('valid_until').select_related('currency')
        d = {}
        # Ordering means that most recent prices overwrite older ones
        for price in qs:
            d[(price.currency.name, price.days)] = price

        d2 = {}
        for price in d.values():
            d2.setdefault(price.currency, []).append(price)

        for key in d2.keys():
            d2[key].sort(key=lambda p: p.days)

        return d2.items()

    def usable(self):
        return self.get_query_set().filter(valid_until__gte=timezone.now())


class Price(models.Model):
    currency = models.ForeignKey(Currency)
    amount = models.DecimalField(decimal_places=2, max_digits=10)

    days = models.PositiveSmallIntegerField()
    description = models.CharField(max_length=255)

    # By having 'valid_until' and creating new rows when changing the price, we
    # can accept payments that are started just before the new price was set.
    valid_until = models.DateTimeField()

    # A Price will be displayed if it is active and has the most recent
    # 'valid_until'
    active = models.BooleanField()

    objects = PriceManager()

    def __unicode__(self):
        return u"%s%s for %s" % (self.currency.symbol, self.amount, self.description)


class Fund(models.Model):
    name = models.CharField(max_length=255, help_text="e.g. 'church' or 'family'")
    manager = models.ForeignKey(Account, related_name='funds_managed')
    balance = models.DecimalField(decimal_places=2, max_digits=10, default=Decimal('0.00'))
    currency = models.ForeignKey(Currency)
    members = models.ManyToManyField(Account, related_name='funds_available', blank=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.manager.username)

class PaymentManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return super(PaymentManager, self).get_query_set().select_related('account')


class Payment(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    # A payment can go against a Fund or an Account, but not both.
    account = models.ForeignKey(Account, null=True, blank=True, related_name='payments')
    fund = models.ForeignKey(Fund, null=True, blank=True, related_name='payments')
    paypal_ipn = models.ForeignKey(PayPalIPN)
    created = models.DateTimeField()

    objects = PaymentManager()

    def __unicode__(self):
        return u"Payment: %s to %s" % (self.amount, self.account if self.account else u"fund '%s'" % self.fund)

import payments.hooks
