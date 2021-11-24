from django.urls import reverse

from common.utils.html import link


def group_url(group):
    return reverse("group", args=(group.slug,))


def group_link(group):
    return link(group_url(group), group.name)
