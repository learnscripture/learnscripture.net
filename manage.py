#!/usr/bin/env python
import logging
import logging.config
import os
import sys
import warnings

if __name__ == "__main__":
    warnings.filterwarnings("always", category=DeprecationWarning)
    warnings.filterwarnings("always", category=PendingDeprecationWarning)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learnscripture.settings")

    from django.conf import settings  # NOQA isort:skip
    from django.core import management  # NOQA isort:skip
    from django.core.management import execute_from_command_line

    logging.config.dictConfig(settings.LOGGING)
    logger = logging.getLogger("manage.py")

    if 'runserver' in sys.argv or 'test' in sys.argv:
        # Development only: Monkey patch `run_checks` to activate a locale, otherwise
        # our django-ftl bundle throws exceptions (presumably due to checks
        # forcing labels etc. to be evaluated).

        # We monkey patch the version in django.core.management.base. This is run
        # as part of:
        #  - runserver
        #  - test setup
        #
        # We don't want to just to `activate`, because then any real issues
        # could be silenced.
        from django_ftl import override
        import django.core.management.base

        run_checks = django.core.management.base.checks.run_checks

        def new_run_checks(*args, **kwargs):
            with override(settings.LANGUAGE_CODE, deactivate=True):
                return run_checks(*args, **kwargs)

        django.core.management.base.checks.run_checks = new_run_checks
    try:
        execute_from_command_line(sys.argv)
    except Exception:
        logger.exception(" ".join(sys.argv))
        raise
