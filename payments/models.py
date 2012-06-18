from decimal import Decimal, ROUND_DOWN
import operator

from django.contrib.sites.models import get_current_site
from django.core import mail
from django.db import models
from django.utils import timezone
from django.template import loader
from paypal.standard.ipn.models import PayPalIPN

from accounts.models import Account


ONE_YEAR = 366 # cover leap years.


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
    def current_prices(self, with_discount=None):
        """
        Get a list of prices, as a list of (currency, [list of Price objects]) tuples

        If 'with_discount' is provided (a fraction as a Decimal), each price object will have
        an attribute 'amount_with_discount'. If 'with_discount' is not 0, the price
        object will have price.discounted == True
        """
        qs = self.get_query_set().filter(active=True).order_by('valid_until').select_related('currency')
        d = {}
        for price in qs:
            price.apply_discount(with_discount)
            # Ordering of queryset means that most recent prices overwrite older
            # ones for the same currency/days combination.
            d[(price.currency.name, price.days)] = price

        d2 = {}
        for price in d.values():
            d2.setdefault(price.currency, []).append(price)

        for key in d2.keys():
            d2[key].sort(key=lambda p: p.days)

        return d2.items()

    def usable(self):
        return self.get_query_set().filter(valid_until__gte=timezone.now())

    def get_current(self, **kwargs):
        return self.get_query_set().filter(**kwargs).order_by('-valid_until')[0]


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

    def get_savings(self, relative_to):
        """
        Returns the savings this price has relative to another price
        (assuming same currency). Works of 'amount_with_discount', not 'amount'
        """
        if self.days == relative_to.days:
            return None
        expected = relative_to.amount_with_discount * Decimal(1.0 * self.days / relative_to.days)
        return (expected - self.amount_with_discount).quantize(Decimal('0.01'),
                                                                rounding=ROUND_DOWN)

    def apply_discount(self, discount):
        """
        Adds 'amount_with_discount' attribute.
        """
        a = self.amount
        if discount is not None and discount != Decimal('0.00'):
            a = (a - discount * a).quantize(Decimal('0.1'), rounding=ROUND_DOWN).quantize(Decimal('0.01'))
            self.discounted = True
        self.amount_with_discount = a


class Fund(models.Model):
    name = models.CharField(max_length=255, help_text="e.g. 'church' or 'family'")
    manager = models.ForeignKey(Account, related_name='funds_managed')
    balance = models.DecimalField(decimal_places=2, max_digits=10, default=Decimal('0.00'))
    currency = models.ForeignKey(Currency)
    members = models.ManyToManyField(Account, related_name='funds_available', blank=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.manager.username)

    def save(self, **kwargs):
        # We avoid updating 'balance' to avoid race conditions that could
        # overwrite this field and effectively cancel an incoming payment

        if self.id is None:
            return super(Fund, self).save(**kwargs)
        else:
            update_fields = [f for f in self._meta.fields if
                             f.name not in ('id', 'balance')]
            update_kwargs = dict((f.name, getattr(self, f.attname)) for
                                 f in update_fields)
            Fund.objects.filter(id=self.id).update(**update_kwargs)


    def receive_payment(self, ipn_obj):
        self.payments.create(amount=ipn_obj.mc_gross,
                             paypal_ipn=ipn_obj,
                             created=timezone.now())
        # Avoid race conditions by only using UPDATE for this field
        Fund.objects.filter(id=self.id).update(balance=models.F('balance') + ipn_obj.mc_gross)
        send_fund_payment_received_email(self, ipn_obj)

    def get_price_object(self):
        return Price.objects.get_current(days=ONE_YEAR, currency=self.currency)

    def price_for(self, account):
        price = self.get_price_object()
        price.apply_discount(self.overall_discount(account))
        return price

    def fund_discount(self):
        member_count = self.members.count()
        if member_count >= 10:
            return Decimal('0.10')
        elif member_count >= 50:
            return Decimal('0.20')
        else:
            return Decimal('0.00')

    def overall_discount(self, account):
        return chain_discounts(account.subscription_discount(), self.fund_discount())

    def can_pay_for(self, account):
        if not self.members.filter(id=account.id).exists():
            return False
        return self.balance >= self.price_for(account).amount_with_discount

    def pay_for(self, account):
        assert self.can_pay_for(account)
        price = self.price_for(account)
        Fund.objects.filter(id=self.id).update(
            balance=models.F('balance') - price.amount_with_discount)
        account.update_subscription_for_price(price)


def chain_discounts(*discounts):
    return Decimal('1.00') - reduce(operator.mul, [Decimal('1.00') - d for d in discounts])


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


def send_fund_payment_received_email(fund, payment):
    from django.conf import settings
    account = fund.manager
    c = {
        'site': get_current_site(None),
        'payment': payment,
        'account': account,
        'fund': fund,
        }

    body = loader.render_to_string("learnscripture/fund_payment_received_email.txt", c)
    subject = u"LearnScripture.net - payment received"
    mail.send_mail(subject, body, settings.SERVER_EMAIL, [account.email])


import payments.hooks
