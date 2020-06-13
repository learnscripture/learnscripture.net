import re

from django.conf import settings
from django.urls import reverse

from .mailgun import create_route, create_webhook, list_routes, update_route, update_webhook

# Almost all emails  go to one person at the moment.
MAINTAINER = "luke@learnscripture.net"
MAINTAINER_REAL = "L.Plant.98@cantab.net"

EMAIL_ADDRESSES = [
    # source, [dest] pairs
    ("admin@learnscripture.net",
     [MAINTAINER]),

    (settings.CONTACT_EMAIL,  # contact form
     [MAINTAINER]),

    ("paypal@learnscripture.net",
     [MAINTAINER]),

    ("sentry@learnscripture.net",
     [MAINTAINER]),

    ("webmaster@learnscripture.net",
     [MAINTAINER]),

    (settings.SERVER_EMAIL,  # if people reply to automated email
     [MAINTAINER]),

    (MAINTAINER,
     [MAINTAINER_REAL]),
]


# See https://mailgun.com/app/routes
def setup_mailgun_routes():
    existing_routes = list_routes()['items']
    existing_d = {i['description']: i for i in existing_routes}

    def update_or_create(name, expression, action, priority=None):
        if name in existing_d:
            route = existing_d[name]
            update_route(route['id'],
                         name,
                         expression,
                         actions,
                         priority=priority)
        else:
            create_route(name,
                         expression,
                         actions,
                         priority=priority)

    for email, destination_emails in EMAIL_ADDRESSES:
        pattern = f'^{re.escape(email)}$'
        expression = f"""match_recipient('{pattern}')"""
        actions = [f"""forward("{d}")""" for d in destination_emails] + ["stop()"]
        update_or_create(email.split('@')[0], expression, actions, priority=5)


def setup_mailgun_webhooks():
    domain = "https://learnscripture.net"
    webhook_bounce_url = domain + reverse("mailgun-bounce-notification")
    try:
        create_webhook('bounce', webhook_bounce_url)
    except Exception:
        update_webhook('bounce', webhook_bounce_url)
