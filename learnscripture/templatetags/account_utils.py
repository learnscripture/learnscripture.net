import logging

from django.template import Library
from django.urls import reverse

from common.utils.html import link
from groups.utils import group_link

register = Library()

logger = logging.getLogger(__name__)


@register.filter
def account_link(account):
    if account.is_erased:
        return "[deleted]"
    return link(
        reverse("user_stats", args=(account.username,)),
        account.username,
        title=f"{account.first_name} {account.last_name}",
    )


register.filter("group_link", group_link)
