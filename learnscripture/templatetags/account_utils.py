from django.core.urlresolvers import reverse
from django.template import Library

from learnscripture.utils.html import html_fragment

register = Library()

@register.filter
def account_link(account):
    return html_fragment('<a href="%s" title="%s %s">%s</a>',
                         reverse('user_stats', args=(account.username,)),
                         account.first_name,
                         account.last_name,
                         account.username,
                         )

from groups.utils import group_link

register.filter('group_link', group_link)
