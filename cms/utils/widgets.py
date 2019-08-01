from django import forms
from django.contrib.admin.widgets import AdminFileWidget
from django.db.models.fields.files import ImageFieldFile
from django.utils.html import format_html, format_html_join

from .images import DETAIL_THUMBNAIL_OPTIONS, ThumbnailException, get_thumbnail


class CmsTextarea(forms.Textarea):

    def render(self, name, value, attrs=None, renderer=None):
        attrs['class'] = 'cms-editor'
        return super(CmsTextarea, self).render(name, value, attrs=attrs, renderer=renderer)


class AdminImageWidgetWithPreview(AdminFileWidget):
    """
    A Widget for an ImageField with a preview of the current image.
    """
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and isinstance(value, ImageFieldFile):
            file_name = str(value)
            try:
                thumbnail = get_thumbnail(file_name, thumbnail_options=DETAIL_THUMBNAIL_OPTIONS)
                if thumbnail:
                    output.append(format_html('<img src="{0}" width="{1}" height="{2}" />', thumbnail.url, thumbnail.width, thumbnail.height))
            except ThumbnailException as e:
                output.append(format_html('<p>{0}</p>', str(e)))
        output.append(super(AdminImageWidgetWithPreview, self).render(name, value, attrs=attrs, renderer=renderer))
        return format_html_join('', '{0}', [(o,) for o in output])
