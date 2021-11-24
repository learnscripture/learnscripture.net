import gzip
import logging
import os.path

from django.core import serializers
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


TEXTVERSION_TEMPLATE = "{0}.TextVersion.json.gz"
CATECHISM_ITEM_TEMPLATE = "{0}.QAPair.json.gz"
BIBLE_ITEM_TEMPLATE = "{0}.Verse.json.gz"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("output_dir")
        parser.add_argument("version_slug", nargs="+")

    def handle(self, *args, **options):
        from bibleverses.models import TextType, TextVersion

        output_dir = options["output_dir"]
        common_options = dict(
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            indent=4,
        )
        format = "json"
        for version_slug in options["version_slug"]:
            print(f"Dumping {version_slug}")
            version = TextVersion.objects.get(slug=version_slug)
            text_file = TEXTVERSION_TEMPLATE.format(version_slug)
            with gzip.open(os.path.join(output_dir, text_file), "wb") as f1:
                serializers.serialize(format, [version], stream=str_to_bytes(f1), **common_options)

            if version.text_type == TextType.CATECHISM:
                items_file = CATECHISM_ITEM_TEMPLATE.format(version_slug)
                items = version.qapairs.all()
            elif version.text_type == TextType.BIBLE:
                items_file = BIBLE_ITEM_TEMPLATE.format(version_slug)
                items = version.verse_set.all()
                for item in items:
                    item.text_fetched_at = None

            with gzip.open(os.path.join(output_dir, items_file), "wb") as f2:
                serializers.serialize(format, items, stream=str_to_bytes(f2), **common_options)


def str_to_bytes(writer):
    class BytesWriter(writer.__class__):
        def write(self, data):
            return super().write(data.encode("utf-8"))

    writer.__class__ = BytesWriter  # Slightly hacky *ahem*
    return writer
