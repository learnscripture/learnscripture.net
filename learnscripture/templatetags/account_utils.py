import logging

from django.core.urlresolvers import reverse
from django.template import Library

from learnscripture.utils.html import html_fragment

register = Library()

logger = logging.getLogger(__name__)

@register.filter
def account_link(account):
    if not account.is_active:
        logger.warning("Account link generated for inactive account %s", account,
                       extra={'request', request})
    return html_fragment(u'<a href="%s" title="%s %s">%s</a>',
                         reverse('user_stats', args=(account.username,)),
                         account.first_name,
                         account.last_name,
                         account.username,
                         )

from groups.utils import group_link

register.filter('group_link', group_link)
