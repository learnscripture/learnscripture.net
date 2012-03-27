from django.db import models


class Currency(models.Model):
    name = models.CharField(max_length=10)
    symbol = models.CharField(max_length=10)

    def __repr__(self):
        return u"<Currency %s>" % self.name

    def __unicode__(self):
        return self.name

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
