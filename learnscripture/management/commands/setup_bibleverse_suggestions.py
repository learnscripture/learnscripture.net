from __future__ import unicode_literals

import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger("bibleverses.suggestions")


class Command(BaseCommand):
    args = '<version_slug version_slug ...>'

    def handle(self, *args, **options):
        from bibleverses.suggestions import generate_suggestions
        from bibleverses.models import TextVersion

        versions = TextVersion.objects.all()
        if args:
            versions = versions.filter(slug__in=list(args))
        for v in versions:
            logger.info("Generating suggestions for %s", v.slug)
            generate_suggestions(v, missing_only=True)
