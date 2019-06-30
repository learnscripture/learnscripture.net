import os

from django.conf import settings
from django.core.files.images import get_image_dimensions
from django.db import models
from django.utils.html import format_html
from mptt.managers import TreeManager
from mptt.models import MPTTModel

from . import managers
from .utils.fields import CmsHTMLField
from .utils.images import LIST_THUMBNAIL_OPTIONS, ThumbnailException, get_thumbnail, get_thumbnail_url

IMAGES_DIR = 'uploads/images'
FILES_DIR = 'uploads/files'


class ContentItem(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)

    objects = managers.ContentItemManager()

    class Meta:
        verbose_name = 'content item'
        verbose_name_plural = 'content items'

    def __str__(self):
        return self.name or '[ UNNAMED ]'


class Content(models.Model):
    content_item = models.ForeignKey(ContentItem, related_name='content_set', on_delete=models.CASCADE)
    language_code = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )
    content_html = CmsHTMLField(verbose_name='Content')

    def __str__(self):
        return '{0}: {1}'.format(self.language_code.upper(), str(self.content_item))

    class Meta:
        unique_together = [
            ('content_item', 'language_code'),
        ]


class Page(MPTTModel):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subpages', verbose_name='parent', on_delete=models.CASCADE)
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
        return self.url

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

    def is_first_child(self):
        if self.is_root_node():
            return True
        return self.parent and (self.lft == self.parent.lft + 1)

    def is_last_child(self):
        if self.is_root_node():
            return True
        return self.parent and (self.rght + 1 == self.parent.rght)

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

    def is_public_for_user(self, user):
        return user.is_staff or self.is_public


class PageTitle(models.Model):
    page = models.ForeignKey(Page, related_name='titles', on_delete=models.CASCADE)
    language_code = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )
    title = models.CharField(max_length=255)

    def __str__(self):
        return '{0}: {1}'.format(self.language_code.upper(), self.title)

    class Meta:
        unique_together = [
            ('page', 'language_code'),
        ]


class PageContentItem(models.Model):
    content_item = models.ForeignKey(ContentItem, related_name='page_content_items', on_delete=models.CASCADE)
    page = models.ForeignKey(Page, related_name='page_content_items', on_delete=models.CASCADE)
    block_name = models.CharField(max_length=255)
    sort = models.IntegerField(blank=True, null=True)


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
