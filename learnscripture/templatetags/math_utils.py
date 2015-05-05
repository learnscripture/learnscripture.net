from decimal import Decimal

from django import template

register = template.Library()
from django.template.defaultfilters import floatformat


@register.filter
def percent(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str((value * Decimal('100')).quantize(Decimal('1'))) + '%'
    return floatformat(value * 100.0, 2) + '%'
