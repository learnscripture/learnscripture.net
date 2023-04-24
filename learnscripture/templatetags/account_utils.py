import logging

from django.template import Library
from django.urls import reverse

from accounts.models import Account
from common.utils.html import link
from groups.models import group_link

from ..utils.urls import build_login_url, build_preferences_url, build_signup_url

register = Library()

logger = logging.getLogger(__name__)


@register.filter
def account_link(account: Account):
    if account.is_erased:
        return "[deleted]"
    return link(
        reverse("user_stats", args=(account.username,)),
        account.username,
        title=f"{account.first_name} {account.last_name}",
    )


register.filter("group_link", group_link)


@register.simple_tag(takes_context=True)
def make_signup_url(context):
    return build_signup_url(context.get("request", None))


@register.simple_tag(takes_context=True)
def make_login_url(context):
    return build_login_url(context.get("request", None))


@register.simple_tag(takes_context=True)
def make_preferences_url(context):
    return build_preferences_url(context.get("request", None))
