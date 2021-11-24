from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer

DETAIL_THUMBNAIL_OPTIONS = {"size": (228, 228)}
LIST_THUMBNAIL_OPTIONS = {"size": (111, 111)}


class ThumbnailException(Exception):
    pass


def get_thumbnail(image, thumbnail_options):
    try:
        thumbnailer = get_thumbnailer(image)
        thumbnail = thumbnailer.get_thumbnail(thumbnail_options)
        return thumbnail
    except InvalidImageFormatError as e:
        raise ThumbnailException(str(e))
    except OSError as e:
        raise ThumbnailException(str(e))


def get_thumbnail_url(image, thumbnail_options):
    try:
        thumbnail = get_thumbnail(image, thumbnail_options)
        if thumbnail:
            return thumbnail.url
    except ThumbnailException:
        return
    return
