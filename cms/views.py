from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect
from django.template.response import TemplateResponse

from .models import Page


def cms_page(request):
    url = request.path_info
    page = Page.objects.get_by_url(url)
    if page is None:
        if not url.endswith('/') and settings.APPEND_SLASH:
            return HttpResponsePermanentRedirect('%s/' % url)
        else:
            raise Http404

    if not page.is_public_for_user(request.user):
        raise Http404

    template_name = page.template_name or settings.CMS_DEFAULT_TEMPLATE
    if page.redirect_page and page.redirect_page != page:  # prevent redirecting to itself
        return HttpResponsePermanentRedirect(page.redirect_page.get_absolute_url())
    context = {
        'cms_page': page
    }
    return TemplateResponse(request, template_name, context)
