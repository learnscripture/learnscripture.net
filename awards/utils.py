from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe


def award_url(award):
    return reverse('award', args=(award.award_detail.slug(),))


def award_link(award):
    return mark_safe(u"<a href='%s'>%s</a>" % (escape(award_url(award)),
                                               escape(award.short_description())))
