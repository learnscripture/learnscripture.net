import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger("bibleverses.suggestions")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("version_slug", nargs="*")
        parser.add_argument(
            "--recreate",
            action="store_true",
            default=False,
            help="If supplied, suggestions will be created even if already existing",
        )

    def handle(self, *args, **options):
        from bibleverses.models import TextVersion
        from bibleverses.suggestions.modelapi import generate_suggestions

        settings.LOADING_WORD_SUGGESTIONS = True

        versions = TextVersion.objects.all()
        slugs = options["version_slug"]
        if slugs:
            versions = versions.filter(slug__in=slugs)
        for v in versions:
            logger.info("Generating suggestions for %s", v.slug)
            generate_suggestions(v, missing_only=not options["recreate"])
