from django.core.urlresolvers import reverse
from django.template import Library
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = Library()

def account_link(account):
    return mark_safe("""<a href="%s" title="%s %s">%s</a>""" % (
            escape(reverse('user_stats', args=(account.username,))),
            escape(account.first_name),
            escape(account.last_name),
            escape(account.username),
            ))

register.filter('account_link', account_link)
