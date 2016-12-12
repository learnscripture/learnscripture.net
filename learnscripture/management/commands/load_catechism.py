import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = 'version_slug json_filename'

    def handle(self, version_slug, json_filename, **options):

        from bibleverses.models import TextVersion, WordSuggestionData
        version = TextVersion.objects.get(slug=version_slug)
        json_data = json.load(file(json_filename))

        settings.LOADING_VERSES = True
        version.qapairs.all().delete()
        WordSuggestionData.objects.filter(version_slug=version.slug).delete()

        # Need to be able to handle things like question "2a"
        for item_num, (number, question, answer) in enumerate(json_data):
            version.qapairs.create(reference="Q{0}".format(number),
                                   question=question,
                                   answer=answer,
                                   order=item_num)
