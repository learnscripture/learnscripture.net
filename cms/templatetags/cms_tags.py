from copy import copy

from django import template

register = template.Library()


@register.inclusion_tag('cms/content_items.html', takes_context=True)
def show_page_content(context, block_name):
    """
    Fetch and render named content items for the current CMS page

    {% show_page_content "block_name" %}              use cms_page in context for content items lookup
    """
    page = context['cms_page']
    page_content_items = page.page_content_items.filter(block_name=block_name).order_by('sort').select_related('content_item')
    content_items = []
    for page_content_item in page_content_items:
        content_item = page_content_item.content_item
        content_item.page_content_item = page_content_item
        content_items.append(content_item)

    context = copy(context)
    context.update({
        'cms_page': page,
        'cms_block_name': block_name,
        'cms_content_items': content_items
    })
    return context
