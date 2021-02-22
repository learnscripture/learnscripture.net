#!/usr/bin/env python
import os
import warnings

warnings.simplefilter("once", PendingDeprecationWarning)
warnings.simplefilter("once", DeprecationWarning)

os.environ['DJANGO_SETTINGS_MODULE'] = 'learnscripture.settings_local'

from django.core import management  # noqa isort:skip
if __name__ == "__main__":
    import learnscripture.checks_monkeypatch  # noqa
    management.execute_from_command_line()
