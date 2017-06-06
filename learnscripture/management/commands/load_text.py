from __future__ import unicode_literals, print_function

import logging
import os.path

from django.db import transaction
from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('input_dir')
        parser.add_argument('version_slug', nargs='+')

    def handle(self, *args, **options):
        from bibleverses.models import TextType

        settings.LOADING_VERSES = True

        input_dir = options['input_dir']
        common_options = dict(
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
        )
        format = 'json'
        for version_slug in options['version_slug']:
            print("Loading {0}".format(version_slug))
            with transaction.atomic():
                text_file = "{0}.TextVersion.json".format(version_slug)
                with file(os.path.join(input_dir, text_file), "rb") as f1:
                    objs = list(serializers.deserialize(format, f1, **common_options))
                    assert len(objs) == 1
                    obj = objs[0]
                    version = obj.object
                    assert version.slug == version_slug
                    obj.save()

                if version.text_type == TextType.CATECHISM:
                    items_file = "{0}.QAPair.json".format(version_slug)
                elif version.text_type == TextType.BIBLE:
                    items_file = "{0}.Verse.json".format(version_slug)

                with file(os.path.join(input_dir, items_file), "rb") as f2:
                    for i, obj in enumerate(serializers.deserialize(format, f2, **common_options)):
                        obj.save()
                        if (i + 1) % 100 == 0:
                            print("Item {0} loaded.".format(i + 1))
