from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core import mail
from django.template import loader
from paypal.standard.ipn.signals import valid_ipn_received, invalid_ipn_received

from accounts.models import Account
from payments.models import DonationDrive, send_donation_drive_target_reached_emails
from payments.sign import unsign_payment_string
from payments.signals import donation_drive_contributed_to, target_reached


def site_address_url_start():
    """
    Returns start of URL (protocol and domain) for this site (a guess)
    """
    protocol = 'https' if settings.SESSION_COOKIE_SECURE else 'http'  # best guess
    return protocol + '://' + get_current_site(None).domain


def send_unrecognised_payment_email(ipn_obj):
    c = {
        'url_start': site_address_url_start(),
        'ipn_obj': ipn_obj,
    }

    body = loader.render_to_string("learnscripture/unrecognised_payment_email.txt", c)
    subject = u"LearnScripture.net - unrecognised payment"
    mail.send_mail(subject, body, settings.SERVER_EMAIL, [settings.DEFAULT_FROM_EMAIL])


def unrecognised_payment(sender, **kwargs):
    send_unrecognised_payment_email(sender)


def paypal_payment_received(sender, **kwargs):
    ipn_obj = sender
    info = unsign_payment_string(ipn_obj.custom)
    if info is None:
        unrecognised_payment(ipn_obj)
        return

    if ipn_obj.payment_status.lower().strip() != 'completed':
        unrecognised_payment(ipn_obj)
        return

    if settings.VALID_RECEIVE_CURRENCY not in (ipn_obj.mc_currency, ipn_obj.settle_currency):
        unrecognised_payment(ipn_obj)
        return

    if ipn_obj.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
        unrecognised_payment(ipn_obj)
        return

    if 'account' in info:
        paypal_account_payment_received(ipn_obj, info)
    else:
        unrecognised_payment(ipn_obj)

    handle_possible_donation_drive_contribution(ipn_obj)


def paypal_account_payment_received(ipn_obj, info):
    try:
        account = Account.objects.get(id=info['account'])
        account.receive_payment(ipn_obj)
    except Account.DoesNotExist:
        unrecognised_payment(ipn_obj)


def handle_possible_donation_drive_contribution(ipn_obj):
    drives = DonationDrive.objects.filter(
        active=True,
        start__lt=ipn_obj.created_at,
        finish__gt=ipn_obj.created_at,
    )
    for d in drives:
        donation_drive_contributed_to.send(d, ipn_obj=ipn_obj)


def donation_drive_contributed_to_handler(sender, ipn_obj=None, **kwargs):
    drive = sender
    if drive.target > 0 and drive.target_reached:
        if not (drive.get_amount_raised(before=ipn_obj.created_at) >= drive.target):
            # We've just over the threshhold
            target_reached.send(drive)


def target_reached_handler(sender, **kwargs):
    drive = sender
    send_donation_drive_target_reached_emails(drive)


donation_drive_contributed_to.connect(donation_drive_contributed_to_handler)
target_reached.connect(target_reached_handler)
valid_ipn_received.connect(paypal_payment_received)
invalid_ipn_received.connect(unrecognised_payment)
