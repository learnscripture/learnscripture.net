from django.core.urlresolvers import reverse

from learnscripture.utils.html import html_fragment

def award_url(award):
    return reverse('award', args=(award.award_detail.slug(),))


def award_link(award):
    return html_fragment(u"<a href='%s'>%s</a>",
                         award_url(award),
                         award.short_description())
