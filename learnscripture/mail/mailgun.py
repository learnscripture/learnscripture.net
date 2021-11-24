# Mailgun specific things.
import hashlib
import hmac
import logging

import requests
from django.conf import settings
from django.utils.crypto import constant_time_compare

logger = logging.getLogger("learnscripture.mail.mailgun")


# See https://documentation.mailgun.com/user_manual.html#securing-webhooks
def verify_webhook(api_key, token, timestamp, signature):
    return constant_time_compare(
        signature, hmac.new(key=api_key, msg=timestamp + token, digestmod=hashlib.sha256).hexdigest()
    )


def api_request(path, data=None, files=None, method=None):
    url = "https://api.mailgun.net/v3"
    url += path

    if method is None:
        if data is None and files is None:
            method = "get"
        else:
            method = "post"

    response = requests.request(method, url, auth=("api", settings.MAILGUN_API_KEY), data=data, files=files)
    response.raise_for_status()
    return response.json()


def list_routes():
    return api_request("/routes")


def create_route(description, expression, actions, priority=None):
    if priority is None:
        priority = 0
    return api_request(
        "/routes", data=dict(description=description, expression=expression, action=actions, priority=priority)
    )


def update_route(id, description, expression, actions, priority=None):
    if priority is None:
        priority = 0
    return api_request(
        f"/routes/{id}",
        method="put",
        data=dict(description=description, expression=expression, action=actions, priority=priority),
    )


def update_webhook(name, url):
    return api_request(f"/domains/{settings.MAILGUN_DOMAIN}/webhooks/{name}", method="put", data=dict(url=url))


def create_webhook(name, url):
    return api_request(f"/domains/{settings.MAILGUN_DOMAIN}/webhooks", data=dict(id=name, url=url))
