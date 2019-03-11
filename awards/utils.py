from django.urls import reverse

from common.utils.html import link


def award_url(award):
    return reverse('award', args=(award.award_detail.slug(),))


def award_link(award):
    return link(award_url(award), award.short_description())
