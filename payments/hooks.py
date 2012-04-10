from django.conf import settings
from django.core import mail
from django.contrib.sites.models import get_current_site
from django.template import loader
from paypal.standard.ipn.signals import payment_was_successful, payment_was_flagged

from accounts.models import Account
from payments.models import Price
from payments.sign import unsign_payment_string

def site_address_url_start():
    """
    Returns start of URL (protocol and domain) for this site (a guess)
    """
    protocol = 'https' if settings.SESSION_COOKIE_SECURE else 'http' # best guess
    return protocol + '://' + get_current_site(None).domain


def send_unrecognised_payment_email(ipn_obj):
    c = {
        'url_start': site_address_url_start(),
        'ipn_obj': ipn_obj,
        }

    body = loader.render_to_string("learnscripture/unrecognised_payment_email.txt", c)
    subject = u"LearnScripture.net - unrecognised payment"
    mail.send_mail(subject, body, settings.SERVER_EMAIL, [settings.DEFAULT_FROM_EMAIL])


def unrecognised_payment(ipn_obj, **kwargs):
    send_unrecognised_payment_email(ipn_obj)


def paypal_payment_received(sender, **kwargs):
    ipn_obj = sender
    d = unsign_payment_string(ipn_obj.custom)
    if d is None:
        unrecognised_payment(ipn_obj)
        return

    try:
        account = Account.objects.get(id=d['account'])
        price = Price.objects.usable().get(id=d['price'])
        if price.amount != ipn_obj.mc_gross:
            unrecognised_payment(ipn_obj)
            return
        if price.currency.name != ipn_obj.mc_currency:
            unrecognised_payment(ipn_obj)
            return
        account.receive_payment(price, ipn_obj)
    except (Account.DoesNotExist, Price.DoesNotExist):
        unrecognised_payment(ipn_obj)


payment_was_successful.connect(paypal_payment_received)
payment_was_flagged.connect(unrecognised_payment)
