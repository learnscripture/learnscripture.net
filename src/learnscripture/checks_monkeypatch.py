import django.core.checks
import django.core.management.base
from django.conf import settings
from django_ftl import override

# We pass `require_activate=True` to our django-ftl Bundle, as per:
# https://django-ftl.readthedocs.io/en/latest/usage.html#lazy-translations

# This gives us problems with `run_checks`, which apparently forces
# evaluation of lazy translation strings.

# So we monkey patch `run_checks` to activate a locale. We don't want to just to
# `activate`, because then any real issues could be silenced, so instead use
# `override` so that after checks has run we are back to having no locale active

run_checks = django.core.management.base.checks.run_checks


def new_run_checks(*args, **kwargs):
    with override(settings.LANGUAGE_CODE):
        return run_checks(*args, **kwargs)


# Used by runserver and test setup:
django.core.management.base.checks.run_checks = new_run_checks

# Used by django-q
django.core.checks.registry.run_checks = new_run_checks
