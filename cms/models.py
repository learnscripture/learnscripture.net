import os

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.files.images import get_image_dimensions
from django.db import models
from django.utils.html import format_html, strip_tags
from mptt.managers import TreeManager
from mptt.models import MPTTModel

from . import managers
from .utils.fields import CmsHTMLField
from .utils.html import htmlentitydecode
from .utils.images import LIST_THUMBNAIL_OPTIONS, ThumbnailException, get_thumbnail, get_thumbnail_url

IMAGES_DIR = 'uploads/images'
FILES_DIR = 'uploads/files'


class ContentItem(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(blank=True, max_length=255)
    content_html = CmsHTMLField(verbose_name='Content')

    objects = managers.ContentItemManager()

    class Meta:
        verbose_name = 'content item'
        verbose_name_plural = 'content items'

    def __str__(self):
        if self.name:
            return self.name
        else:
            contents = u' '.join(htmlentitydecode(strip_tags(self.content_html)).strip().split())
            if len(contents) > 50:
                contents = contents[:50] + '...'
            return contents or '[ EMPTY ]'


class Page(MPTTModel):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subpages', verbose_name='parent', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=1000, blank=True)
    redirect_page = models.ForeignKey('self', null=True, blank=True, related_name='redirected_pages', on_delete=models.SET_NULL)
    template_name = models.CharField(blank=True, max_length=70, choices=settings.CMS_TEMPLATE_CHOICES)
    is_public = models.BooleanField(default=True)
    content_items = models.ManyToManyField(ContentItem, through='PageContentItem')

    objects = managers.PageManager()
    tree = TreeManager()

    class Meta:
        verbose_name = 'page'
        verbose_name_plural = 'pages'
        ordering = ('tree_id', 'lft')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.id:
            old_url = Page.objects.get(id=self.id).get_absolute_url()
        else:
            old_url = ''

        super(Page, self).save(*args, **kwargs)

        if old_url:
            new_url = self.get_absolute_url()
            if old_url != new_url:
                ContentItem.objects.rename_url(old_url, new_url)

    def get_absolute_url(self):
        return self.url

    def get_content_for_block(self, block_name):
        """
        Return sorted content items for this block.
        """
        return self.page_content_items.filter(block_name=block_name).order_by('sort')

    def is_first_child(self):
        if self.is_root_node():
            return True
        return self.parent and (self.lft == self.parent.lft + 1)

    def is_last_child(self):
        if self.is_root_node():
            return True
        return self.parent and (self.rght + 1 == self.parent.rght)

    def is_child_of(self, node):
        """
        Returns True if this is a child of the given node.
        """
        return (self.tree_id == node.tree_id and
                self.lft > node.lft and
                self.rght < node.rght)

    def get_ancestors(self, *args, **kwargs):
        if getattr(self, '_ancestors_retrieved', False):
            # We have already retrieved the chain of parent objects, so can skip
            # a DB query for this.
            ancestors = []
            node = self
            while node.parent_id is not None:
                ancestors.insert(0, node.parent)
                node = node.parent
            return ancestors
        else:
            return super(Page, self).get_ancestors(*args, **kwargs)

    def move_page(self, target_id, position):
        """
        Moves the node. Parameters:
        - target_id: target page
        - position:
            - before: move the page before the target page
            - after: move the page after the target page
            - inside: move the page inside the target page (as the first child)
        """
        old_url = self.get_absolute_url()
        target_page = Page.tree.get(id=target_id)

        if position == 'before':
            self.move_to(target_page, 'left')
        elif position == 'after':
            self.move_to(target_page, 'right')
        elif position == 'inside':
            self.move_to(target_page)
        else:
            raise Exception('Unknown position')

        # change url in content items
        if old_url:
            new_url = self.get_absolute_url()
            if old_url != new_url:
                ContentItem.objects.rename_url(old_url, new_url)

    def is_public_for_user(self, user):
        return user.is_staff or self.is_public


class PageContentItem(models.Model):
    content_item = models.ForeignKey(ContentItem, related_name='page_content_items', on_delete=models.CASCADE)
    page = models.ForeignKey(Page, related_name='page_content_items', on_delete=models.CASCADE)
    block_name = models.CharField(max_length=255)
    sort = models.IntegerField(blank=True, null=True)

    def move(self, next_item_id=None, block_name=None):
        next_item = None
        if next_item_id:
            next_item = PageContentItem.objects.get(pk=next_item_id)
        if not block_name:
            if next_item:
                block_name = next_item.block_name
            else:
                block_name = self.block_name

        if self.block_name != block_name:
            self.block_name = block_name
            self.save()

        page_content_items = list(
            self.page.get_content_for_block(block_name).exclude(id=self.id),
        )

        def resort():
            for i, item in enumerate(page_content_items):
                item.sort = i
                item.save()

        if not next_item:
            page_content_items.append(self)
            resort()
        else:
            if next_item in page_content_items:
                next_index = page_content_items.index(next_item)
                page_content_items.insert(next_index, self)
                resort()


def images_directory(instance, filename):
    return os.path.join(IMAGES_DIR, filename)


class Image(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to=images_directory, max_length=255)
    title = models.CharField(max_length=255)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'image'
        verbose_name_plural = 'images'
        ordering = ('-updated', )

    def __str__(self):
        return self.image.name

    def save(self, *args, **kwargs):
        # delete existing Image(s) with the same image.name - TODO: warn about this?
        existing_images = Image.objects.filter(image=os.path.join(IMAGES_DIR, self.image.name))
        for existing_image in existing_images:
            existing_image.delete()

        self.get_image_information()
        super(Image, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(Image, self).delete(*args, **kwargs)
        self.image.storage.delete(self.image.name)

    def get_image_information(self):
        self.width, self.height = get_image_dimensions(self.image) or (0, 0)

    def get_filename(self):
        return os.path.basename(self.image.name)

    def get_size(self):
        return '%s x %d' % (self.width, self.height)
    get_size.short_description = 'Size'

    def thumbnail(self):
        return get_thumbnail(self.image, thumbnail_options=LIST_THUMBNAIL_OPTIONS)

    def thumbnail_url(self):
        return get_thumbnail_url(self.image, thumbnail_options=LIST_THUMBNAIL_OPTIONS)

    def preview(self):
        try:
            thumbnail = get_thumbnail(self.image, thumbnail_options=LIST_THUMBNAIL_OPTIONS)
            if thumbnail:
                return format_html('<img src="{0}" width="{1}" height="{2}" />', thumbnail.url, thumbnail.width, thumbnail.height)
        except ThumbnailException as e:
            return str(e)
    preview.short_description = 'Preview'


def files_directory(instance, filename):
    return os.path.join(FILES_DIR, filename)


class File(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to=files_directory, max_length=255)
    title = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'file'
        verbose_name_plural = 'files'
        ordering = ('-updated', )

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        # delete existing File(s) with the same file.name - TODO: warn about this?
        existing_files = File.objects.filter(file=os.path.join(FILES_DIR, self.file.name))
        for existing_file in existing_files:
            existing_file.delete()

        super(File, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(File, self).delete(*args, **kwargs)
        self.file.storage.delete(self.file.name)

    def get_filename(self):
        return os.path.basename(self.file.name)
