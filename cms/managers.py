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
                rf"""(\s)href=(["']){old_url}""",
                rf"\1href=\2{new_url}",
                html,
            )

        queryset = self.get_queryset()

        for content_item in queryset:
            html = rename_html(content_item.content_html)

            if html != content_item.content_html:
                content_item.content_html = html
                content_item.save()


class PageManager(TreeManager):
    def get_by_url(self, url):
        """
        Retrieve a page that matches the given URL, or return None if none found
        """
        return self.get_queryset().filter(url=url).first()
