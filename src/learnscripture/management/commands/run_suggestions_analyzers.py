import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger("bibleverses.suggestions")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("version_slug", nargs="*")
        parser.add_argument(
            "--disallow-text-loading",
            action="store_true",
            default=False,
            help="Disallow loading of text (requires that pre-analysis is already done).",
        )

    def handle(self, *args, **options):
        from bibleverses.suggestions.analyze import analyze_all

        analyze_all(
            version_slugs=options.get("version_slug", None), disallow_text_loading=options["disallow_text_loading"]
        )
