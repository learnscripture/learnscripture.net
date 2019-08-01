import django.core.checks
import django.core.management.base
from django.conf import settings
from django_ftl import override

# Development only: Monkey patch `run_checks` to activate a locale, otherwise
# our django-ftl bundle throws exceptions (presumably due to checks
# forcing labels etc. to be evaluated).

# We monkey patch the version in django.core.management.base. This is run
# as part of:
#  - runserver
#  - test setup
#  - celery fixups
#
# We don't want to just to `activate`, because then any real issues
# could be silenced.


run_checks = django.core.management.base.checks.run_checks


def new_run_checks(*args, **kwargs):
    with override(settings.LANGUAGE_CODE):
        return run_checks(*args, **kwargs)


# Used by runserver and test setup:
django.core.management.base.checks.run_checks = new_run_checks

# Used by celery
django.core.checks.run_checks = new_run_checks
