import logging

from django.template import Library
from django.urls import reverse
from django.utils.html import format_html

from groups.utils import group_link

register = Library()

logger = logging.getLogger(__name__)


@register.filter
def account_link(account):
    return format_html(u'<a href="{0}" title="{1} {2}">{3}</a>',
                       reverse('user_stats', args=(account.username,)),
                       account.first_name,
                       account.last_name,
                       account.username,
                       )


register.filter('group_link', group_link)
