from typing import Optional

import attr
import furl


@attr.s(auto_attribs=True)
class Page:
    items: list[object]
    from_item: int
    shown_count: int
    more: bool
    more_link: str
    total: Optional[int] = None

    @property
    def empty(self):
        return len(self.items) == 0 and self.from_item == 0


def get_request_from_item(request):
    try:
        return int(request.GET.get("from_item", "0"))
    except ValueError:
        return 0


def get_paged_results(queryset, request, page_size):
    """
    Return a Page of the queryset, using standard paging mechanism and the page number from the request.
    """
    total = queryset.count()
    from_item = get_request_from_item(request)
    last_item = from_item + page_size
    # Get one extra to see if there is more
    result_page = list(queryset[from_item : last_item + 1])
    more = len(result_page) > page_size
    # Then trim result_page to correct size
    result_page = result_page[0:page_size]
    shown_count = from_item + len(result_page)
    return Page(
        items=result_page,
        from_item=from_item,
        shown_count=shown_count,
        total=total,
        more=more,
        more_link=(
            furl.furl(request.get_full_path()).remove(query=["from_item"]).add(query_params={"from_item": last_item})
        ),
    )
