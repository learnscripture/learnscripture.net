from django.core.urlresolvers import reverse
from learnscripture.utils.html import html_fragment


def group_url(group):
    return reverse('group', args=(group.slug,))


def group_link(group):
    return html_fragment(u"<a href='%s'>%s</a>",
                         group_url(group), group.name)
