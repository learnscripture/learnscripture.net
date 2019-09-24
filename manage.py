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

    import learnscripture.checks_monkeypatch  # noqa
    try:
        execute_from_command_line(sys.argv)
    except Exception:
        logger.exception(" ".join(sys.argv))
        raise
