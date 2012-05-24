from django.core.urlresolvers import reverse


def group_url(group):
    return reverse('group', args=(group.slug,))


def group_link(group):
    return "<a href='%s'>%s</a>" % (group_url(group), group.name)
