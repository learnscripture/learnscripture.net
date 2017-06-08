from django.urls import reverse
from django.utils.html import format_html


def award_url(award):
    return reverse('award', args=(award.award_detail.slug(),))


def award_link(award):
    return format_html("<a href='{0}'>{1}</a>",
                       award_url(award),
                       award.short_description())
