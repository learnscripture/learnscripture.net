from celery.task import task
from django.contrib.sites.models import get_current_site
from django.core import mail
from django.template import loader
from paypal.standard.ipn.models import PayPalIPN


@task(ignore_result=True)
def send_fund_payment_received_email(fund_id, ipn_id):
    from django.conf import settings
    from payments.models import Fund
    fund = Fund.objects.get(id=fund_id)
    payment = PayPalIPN.objects.get(id=ipn_id)
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

