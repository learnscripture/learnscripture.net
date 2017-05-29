from django.urls import reverse
from django.utils.html import format_html


def group_url(group):
    return reverse('group', args=(group.slug,))


def group_link(group):
    return format_html(u"<a href='{0}'>{1}</a>",
                       group_url(group), group.name)
