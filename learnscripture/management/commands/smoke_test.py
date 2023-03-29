import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        from bibleverses.models import TextVersion

        versions = TextVersion.objects.all()
        if len(versions) == 0:
            raise AssertionError("No TextVersions found. Has the database been loaded?")
        if "KJV" not in [v.slug for v in versions]:
            raise AssertionError("KJV not found")

        # Load main entry points to check for import errors
        import learnscripture.urls  # noqa
        import learnscripture.views  # noqa

        print("Smoke test successful")
