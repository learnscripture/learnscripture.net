import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('version_slug')
        parser.add_argument('json_filename')

    def handle(self, *args, **options):
        from bibleverses.models import TextVersion, WordSuggestionData
        version_slug = options['version_slug']
        json_filename = options['json_filename']
        version = TextVersion.objects.get(slug=version_slug)
        json_data = json.load(open(json_filename))

        settings.LOADING_VERSES = True
        version.qapairs.all().delete()
        WordSuggestionData.objects.filter(version_slug=version.slug).delete()

        # Need to be able to handle things like question "2a"
        for item_num, (number, question, answer) in enumerate(json_data):
            version.qapairs.create(localized_reference=f"Q{number}",
                                   question=question,
                                   answer=answer,
                                   order=item_num)
