from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe


def group_url(group):
    return reverse('group', args=(group.slug,))


def group_link(group):
    return "<a href='%s'>%s</a>" % (escape(group_url(group)),
                                    escape(group.name))
