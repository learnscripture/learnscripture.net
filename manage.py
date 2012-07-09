#!/usr/bin/env python
import os, sys
import warnings

if __name__ == "__main__":
    warnings.filterwarnings("always", category=DeprecationWarning)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "learnscripture.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
