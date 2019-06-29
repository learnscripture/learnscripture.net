from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect
from django.template.response import TemplateResponse
from django.utils.functional import cached_property

from .models import Page as Page


class PageWrapper:
    def __init__(self, page):
        self.page = page

    @cached_property
    def blocks(self):
        return Blocks(self)

    def title(self):
        return self.page.title


class Blocks:
    """
    Provides dictionary access to the content items in a block in a Page
    """
    def __init__(self, page_wrapper):
        self.page_wrapper = page_wrapper

    def __getitem__(self, block_name):
        return [
            pci.content_item
            for pci in (
                self.page_wrapper.page.page_content_items
                    .filter(block_name=block_name)
                    .order_by('sort')
                    .select_related('content_item')
            )
        ]


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
        'page': PageWrapper(page)
    }
    return TemplateResponse(request, template_name, context)
