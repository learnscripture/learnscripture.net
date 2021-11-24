import glob
import os
import subprocess

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


# Monkey patch WebpackLoader to call `webpack` just in time.
# This means that tests that don't need to run webpack
# don't have that overhead.

original_get_assets = WebpackLoader.get_assets

_loaded = []


def get_assets(self):
    if not _loaded:
        for f in glob.glob("./learnscripture/static/webpack_bundles/*.tests.*"):
            os.unlink(f)
        subprocess.check_call(["./node_modules/.bin/webpack", "--config", "webpack.config.tests.js"])
        _loaded.append(True)
    return original_get_assets(self)


WebpackLoader.get_assets = get_assets
