import re

from django.db import models
from mptt.managers import TreeManager


class ContentItemManager(models.Manager):

    def rename_url(self, old_url, new_url):
        """
        Change the urls in all content pages. Also changes the urls that begin with this url.
        """

        def rename_html(html):
            return re.sub(
                r"""(\s)href=(["'])%s""" % old_url,
                r'\1href=\2%s' % new_url,
                html,
            )

        queryset = self.get_queryset()

        for content_item in queryset:
            html = rename_html(content_item.content_html)

            if html != content_item.content_html:
                content_item.content_html = html
                content_item.save()


class PageManager(TreeManager):

    def link_parent_objects(self, pages):
        """
        Given an iterable of page objects which includes all ancestors
        of any contained pages, unifies the 'parent' objects
        using items in the iterable.
        """
        pages = list(pages)
        page_dict = {}
        for p in pages:
            page_dict[p.id] = p
        for p in pages:
            if p.parent_id is None:
                p.parent = None
            else:
                p.parent = page_dict[p.parent_id]
            p._ancestors_retrieved = True
        return pages

    def get_by_url(self, url):
        """
        Retrieve a page that matches the given URL, or return None if none found
        """
        return self.get_queryset().filter(url=url).first()
