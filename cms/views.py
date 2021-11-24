import attr
from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect
from django.template.response import TemplateResponse
from django.utils.functional import cached_property

from .models import Content, Page, PageTitle


class PageWrapper:
    def __init__(self, page, language_code):
        self.page = page
        self.language_code = language_code

    @cached_property
    def blocks(self):
        return Blocks(self)

    @property
    def missing_translations(self):
        if not self.title_data.right_language:
            return True
        if any(not c.right_language for c in self.content_list):
            return True
        return False

    @cached_property
    def content_list(self):
        # We get all Content objects for all blocks, for the required language,
        # because we need them for calculating missing_translations. The Blocks
        # wrapper does filtering for block_name in Python, so we need to keep
        # track of that in ContentWrapper.

        # Here we are careful to be fairly efficient about get the ones that are
        # the right language, and also the fallbacks, and indicate that we got
        # the wrong language where necessary.

        blocks_and_content_items = [
            (pci.block_name, pci.content_item)
            for pci in (self.page.page_content_items.order_by("sort").select_related("content_item"))
        ]
        # Collect all
        content_dict = {
            (c.content_item_id, c.language_code): c
            for c in Content.objects.filter(
                content_item__in=[i[1] for i in blocks_and_content_items],
                language_code__in=[self.language_code, settings.LANGUAGE_CODE],
            ).select_related("content_item")
        }
        # Build ContentWrappers
        retval = []
        for block_name, ci in blocks_and_content_items:
            try:
                retval.append(
                    ContentWrapper(
                        content_dict[ci.id, self.language_code],
                        block_name=block_name,
                        right_language=True,
                    )
                )
            except KeyError:
                retval.append(
                    ContentWrapper(
                        content_dict[ci.id, settings.LANGUAGE_CODE],
                        block_name=block_name,
                        right_language=False,
                    )
                )
        return retval

    @cached_property
    def title_data(self):
        try:
            return TitleWrapper(
                title_obj=self.page.titles.get(language_code=self.language_code),
                right_language=True,
            )
        except PageTitle.DoesNotExist:
            return TitleWrapper(
                title_obj=self.page.titles.get(language_code=settings.LANGUAGE_CODE),
                right_language=False,
            )


@attr.s
class TitleWrapper:
    title_obj = attr.ib()
    right_language = attr.ib(type=bool)

    @property
    def title(self):
        return self.title_obj.title


@attr.s
class ContentWrapper:
    content_obj = attr.ib()
    block_name = attr.ib()
    right_language = attr.ib(type=bool)

    @property
    def content_html(self):
        return self.content_obj.content_html


class Blocks:
    """
    Provides dictionary access to the Content objects in a block in a Page
    """

    def __init__(self, page_wrapper):
        self.page_wrapper = page_wrapper

    def __getitem__(self, block_name):
        return [c for c in self.page_wrapper.content_list if c.block_name == block_name]


def cms_page(request):
    url = request.path_info
    page = Page.objects.get_by_url(url)
    if page is None:
        if not url.endswith("/") and settings.APPEND_SLASH:
            return HttpResponsePermanentRedirect(f"{url}/")
        else:
            raise Http404

    if not page.is_public_for_user(request.user):
        raise Http404

    template_name = page.template_name or settings.CMS_DEFAULT_TEMPLATE
    if page.redirect_page and page.redirect_page != page:  # prevent redirecting to itself
        return HttpResponsePermanentRedirect(page.redirect_page.get_absolute_url())
    context = {"page": PageWrapper(page, request.LANGUAGE_CODE)}
    return TemplateResponse(request, template_name, context)
