import os
import subprocess
from pathlib import Path

import filelock
from webpack_loader.loader import WebpackLoader

from .settings_local import *  # noqa
from .settings_local import DATABASES, INSTALLED_APPS, LOGGING, MIDDLEWARE, SRC_ROOT, WEBPACK_LOADER

TESTS_RUNNING = True

INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in ["debug_toolbar", "django_extensions"]]
MIDDLEWARE = [m for m in MIDDLEWARE if m not in ["debug_toolbar.middleware.DebugToolbarMiddleware"]]


DATABASES["default"]["CONN_MAX_AGE"] = 0  # fix some deadlocks with DB flushing

LOGGING["root"] = {
    "level": "WARNING",
    "handlers": ["console"],
}
LOGGING["loggers"]["django_ftl.message_errors"] = {
    "level": "INFO",
    "handlers": ["console"],
    "propagate": False,
}
LOGGING["handlers"]["console"]["level"] = "ERROR"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

TASKS_EAGER = True


WEBPACK_STATS_FILE = "webpack-stats.tests.json"
WEBPACK_LOADER["DEFAULT"]["CACHE"] = True
WEBPACK_LOADER["DEFAULT"]["STATS_FILE"] = os.path.join(SRC_ROOT, WEBPACK_STATS_FILE)


# Monkey patch WebpackLoader to call `webpack`. so that we don't have to run
# webpack before running tests. We do it "just in time", so that tests that
# don't need to run webpack don't have that overhead.

original_get_assets = WebpackLoader.get_assets

# process global to check if Webpack has been run
_webpack_run_once = []


def get_assets(self):
    if not _webpack_run_once:

        def run_webpack():
            subprocess.check_call(["./node_modules/.bin/webpack", "--env", "mode=tests"])

        # For pytest-xdist, we want webpack to run just once, because it is
        # pretty slow. This means we need interprocess communication, but we
        # also want to ensure that subsequent runs also run webpack,
        # irrespective of whether the previous run shut down cleanly.

        # We solve using 1) a file lock and 2) PYTEST_XDIST_TESTRUNUID which is
        # shared across these processes, but not between runs.

        if (run_id := os.environ.get("PYTEST_XDIST_TESTRUNUID", None)) is None:
            # single process, simple case:
            run_webpack()
        else:
            lock = filelock.FileLock(".pytest-xdist.lock")
            with lock:
                run_id_path = Path(".pytest-xdist-run.txt")
                if not run_id_path.exists() or run_id not in run_id_path.read_text():
                    run_webpack()
                    with run_id_path.open("w") as f:
                        f.write(run_id + "\n")
        _webpack_run_once.append(True)
    return original_get_assets(self)


WebpackLoader.get_assets = get_assets
