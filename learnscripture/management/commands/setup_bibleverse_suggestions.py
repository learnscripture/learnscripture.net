from __future__ import unicode_literals

import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = '<version_slug version_slug ...>'

    def handle(self, *args, **options):
        from bibleverses.suggestions import generate_suggestions, get_thesaurus, version_thesaurus
        from bibleverses.models import TextVersion

        thesaurus = get_thesaurus()

        versions = TextVersion.objects.all()
        if args:
            versions = versions.filter(slug__in=list(args))
        for v in versions:
            logger.info("Generating suggestions for %s", v.slug)
            if thesaurus:
                v_thesaurus = version_thesaurus(v, thesaurus)
            else:
                v_thesaurus = None
            generate_suggestions(v, missing_only=True, thesaurus=v_thesaurus)
