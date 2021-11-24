from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Page


@staff_member_required
def page_move_up(request, id):
    # TODO - should be POST only
    page = Page.objects.get(pk=id)

    if page:
        previous_sibling_page = page.get_previous_sibling()
        if previous_sibling_page:
            page.move_to(previous_sibling_page, position="left")

    return HttpResponseRedirect(reverse("admin:cms_page_changelist"))


@staff_member_required
def page_move_down(request, id):
    # TODO - should be POST only
    page = Page.objects.get(pk=id)

    if page:
        next_sibling_page = page.get_next_sibling()
        if next_sibling_page:
            page.move_to(next_sibling_page, position="right")

    return HttpResponseRedirect(reverse("admin:cms_page_changelist"))
