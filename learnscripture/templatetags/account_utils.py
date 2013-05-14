import logging

from django.core.urlresolvers import reverse
from django.template import Library
from django.utils.html import format_html

register = Library()

logger = logging.getLogger(__name__)

@register.filter
def account_link(account):
    if not account.is_active:
        logger.warning("Account link generated for inactive account %s", account)
    return format_html(u'<a href="{0}" title="{1} {2}">{3}</a>',
                       reverse('user_stats', args=(account.username,)),
                       account.first_name,
                       account.last_name,
                       account.username,
                       )

from groups.utils import group_link

register.filter('group_link', group_link)
