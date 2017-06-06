import logging
import os.path

from django.core import serializers
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('output_dir')
        parser.add_argument('version_slug', nargs='+')

    def handle(self, *args, **options):
        from bibleverses.models import TextVersion, TextType
        from bibleverses.services import partial_data_available

        output_dir = options['output_dir']
        common_options = dict(
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            indent=4,
        )
        format = 'json'
        for version_slug in options['version_slug']:
            print("Dumping {0}".format(version_slug))
            version = TextVersion.objects.get(slug=version_slug)
            text_file = "{0}.TextVersion.json".format(version_slug)
            with file(os.path.join(output_dir, text_file), "wb") as f1:
                serializers.serialize(format, [version], stream=f1, **common_options)

            if version.text_type == TextType.CATECHISM:
                items_file = "{0}.QAPair.json".format(version_slug)
                items = version.qapairs.all()
            elif version.text_type == TextType.BIBLE:
                items_file = "{0}.Verse.json".format(version_slug)
                items = version.verse_set.all()
                if partial_data_available(version_slug):
                    items = blank_text_saved(items)

            with file(os.path.join(output_dir, items_file), "wb") as f2:
                serializers.serialize(format, items, stream=f2, **common_options)


def blank_text_saved(items):
    for item in items:
        item.text_saved = ''
        item.text_fetched_at = None
        yield item
