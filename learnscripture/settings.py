# -*- coding: utf-8 -*-
# Django settings for learnscripture project.
import glob
import json
import os
import socket
import subprocess
import sys

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

hostname = socket.gethostname()
CHECK_DEPLOY = 'manage.py check --deploy' in ' '.join(sys.argv)
RUNNING_MIGRATIONS = 'migrate' in sys.argv
if CHECK_DEPLOY:
    LIVEBOX = True
    DEVBOX = False
else:
    LIVEBOX = hostname.startswith('learnscripture')
    DEVBOX = not LIVEBOX


DEBUG = DEVBOX and not RUNNING_MIGRATIONS

# A kitten gets killed every time you use this:
TESTING = 'manage.py test' in ' '.join(sys.argv)


SRC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ../
PROJECT_ROOT = os.path.dirname(SRC_ROOT)
HOME_DIR = os.environ['HOME']

if LIVEBOX:
    LOG_ROOT = os.path.join(HOME_DIR, 'logs')
else:
    LOG_ROOT = os.path.join(PROJECT_ROOT, 'logs')
if not os.path.exists(LOG_ROOT):
    os.system(f"mkdir -p {LOG_ROOT}")

secrets = json.load(open(os.path.join(SRC_ROOT, "config", "secrets.json")))

MAILGUN_API_KEY = secrets.get('MAILGUN_API_KEY', None)
MAILGUN_DOMAIN = 'learnscripture.net'


# See also fabfile.py which defines these
DB_LABEL_DEFAULT = "default"
DB_LABEL_WORDSUGGESTIONS = "wordsuggestions"

if LIVEBOX:
    p = os.path.dirname(os.path.abspath(__file__))

    DATABASES = {
        DB_LABEL_DEFAULT: {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': secrets["PRODUCTION_DB_NAME"],
            'USER': secrets["PRODUCTION_DB_USER"],
            'PASSWORD': secrets["PRODUCTION_DB_PASSWORD"],
            'HOST': 'localhost',
            'PORT': secrets["PRODUCTION_DB_PORT"],
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': 120,
        },
        DB_LABEL_WORDSUGGESTIONS: {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': secrets["PRODUCTION_DB_NAME_WS"],
            'USER': secrets["PRODUCTION_DB_USER"],
            'PASSWORD': secrets["PRODUCTION_DB_PASSWORD"],
            'HOST': 'localhost',
            'PORT': secrets["PRODUCTION_DB_PORT"],
            'ATOMIC_REQUESTS': False,
            'CONN_MAX_AGE': 120,
        }
    }
    SECRET_KEY = secrets["PRODUCTION_SECRET_KEY"]
    SENTRY_DSN = secrets["PRODUCTION_SENTRY_DSN"]
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    ANYMAIL = {
        "MAILGUN_API_KEY": MAILGUN_API_KEY,
    }

else:
    # Development settings:

    # We have problems with wordsuggestions DB connections not being closed in
    # test environment, especially related to the non-default DB it seems,
    # probably a Django bug, so we workaround:
    conn_max_age = 0 if TESTING else 120
    try:
        from .settings_local import DB_USER, DB_PORT
    except ImportError:
        DB_USER = 'learnscripture'
        DB_PORT = 5432

    DATABASES = {
        DB_LABEL_DEFAULT: {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'learnscripture',
            'USER': DB_USER,
            'PASSWORD': 'foo',
            'HOST': 'localhost',
            'PORT': DB_PORT,
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': conn_max_age,
        },
        DB_LABEL_WORDSUGGESTIONS: {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'learnscripture_wordsuggestions',
            'USER': DB_USER,
            'PASSWORD': 'foo',
            'HOST': 'localhost',
            'PORT': DB_PORT,
            'ATOMIC_REQUESTS': False,
            'CONN_MAX_AGE': conn_max_age,
        }
    }

    SECRET_KEY = secrets.get('DEVELOPMENT_SECRET_KEY', "abc123")
    SENTRY_DSN = secrets.get('DEVELOPMENT_SENTRY_DSN', None)

    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


DATABASE_ROUTERS = ['learnscripture.router.LearnScriptureRouter']

AUTH_USER_MODEL = 'accounts.Account'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend'
]

SESSION_COOKIE_AGE = 3600 * 24 * 31 * 4  # 4 months

if LIVEBOX:
    # Can't use in development because we use HTTP locally
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = True


ADMINS = [
    ('', 'admin@learnscripture.net')
]

MANAGERS = ADMINS

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

SERVER_EMAIL = 'website@learnscripture.net'
DEFAULT_FROM_EMAIL = SERVER_EMAIL
CONTACT_EMAIL = 'contact@learnscripture.net'


if DEVBOX:
    PAYPAL_RECEIVER_EMAIL = 'paypal_1314646057_biz@cciw.co.uk'
    PAYPAL_TEST = True
else:
    PAYPAL_RECEIVER_EMAIL = "paypal@learnscripture.net"
    PAYPAL_TEST = False

PAYPAL_BUY_BUTTON_IMAGE = "https://www.paypalobjects.com/en_US/GB/i/btn/btn_buynowCC_LG.gif"

VALID_RECEIVE_CURRENCY = 'GBP'

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('tr', 'Turkçe'),
]
LANGUAGE_CODES = [c for c, n in LANGUAGES]

SITE_ID = 1

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Sync with fabfile
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'usermedia')
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
DATA_ROOT = os.path.join(PROJECT_ROOT, 'data')  # See also bibleverses.storage.suggestions.DATA_ROOT


MEDIA_URL = '/usermedia/'
STATIC_URL = '/static/'

STATICFILES_DIRS = []

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',  # for cms admin
)

LOGIN_URL = '/admin/'

CSRF_FAILURE_VIEW = 'learnscripture.views.csrf_failure'


MIDDLEWARE = [
    m for b, m in
    [
        (True, 'django.middleware.security.SecurityMiddleware'),
        (DEBUG, 'debug_toolbar.middleware.DebugToolbarMiddleware'),
        (True, 'django.contrib.sessions.middleware.SessionMiddleware'),
        (True, 'learnscripture.middleware.pwa_tracker_middleware'),
        (True, 'django.middleware.common.CommonMiddleware'),
        (True, 'django.middleware.csrf.CsrfViewMiddleware'),
        (True, 'django.contrib.auth.middleware.AuthenticationMiddleware'),
        (True, 'learnscripture.middleware.token_login_middleware'),
        (True, 'django.contrib.messages.middleware.MessageMiddleware'),
        (True, 'django.middleware.clickjacking.XFrameOptionsMiddleware'),
        (DEVBOX, 'learnscripture.middleware.debug_middleware'),
        (DEBUG, 'learnscripture.middleware.paypal_debug_middleware'),
        (True, 'learnscripture.middleware.identity_middleware'),
        (True, 'learnscripture.middleware.activate_language_from_request'),
    ]
    if b
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.i18n',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'learnscripture.context_processors.session_forms',
                'learnscripture.context_processors.referral_links',
                'learnscripture.context_processors.menu',
                'learnscripture.context_processors.notices',
                'learnscripture.context_processors.themes',
                'learnscripture.context_processors.settings_processor',
                'learnscripture.context_processors.request_account',
                'learnscripture.context_processors.indexing',
                'learnscripture.context_processors.ftl',
            ],
            'debug': DEBUG,
        },
    },
]

ROOT_URLCONF = 'learnscripture.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'learnscripture.wsgi.application'

INSTALLED_APPS = [
    'dal',  # Needs to be before admin
    'dal_select2',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.humanize',
    # This project
    'learnscripture',
    'bibleverses',
    'accounts',
    'scores',
    'payments',
    'awards',
    'events',
    'groups',
    'comments',
    'cms',

    # Third party
    'mptt',
    'compressor',  # for cms
    'easy_thumbnails',
    'spurl',
    'paypal.standard.ipn',
    'app_metrics',
    'django_markup',
    'anymail',
    'aldjemy',
    'webpack_loader',
    'django_ftl',
    'capture_tag',
]

ALLOWED_HOSTS = ["learnscripture.net"]
if DEVBOX:
    ALLOWED_HOSTS.extend([
        ".ngrok.io",
        "learnscripture.local",
        "localhost",
    ])

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    INSTALLED_APPS.append('django_extensions')  # For runserver_plus


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'bibleservices': {
            'level': 'INFO',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_ROOT, 'bibleservices_debug.log'),
            'maxBytes': 1024 * 1024,
            'backupCount': 10,
        },
        'celerydebug': {
            'level': 'DEBUG',
            'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_ROOT, 'celery_debug.log'),
            'maxBytes': 1024 * 1024,
            'backupCount': 10,
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'level': 'DEBUG',
            'handlers': ['celerydebug'],
            'propagate': True,
        },
        'celerydebug': {
            'level': 'DEBUG',
            'handlers': ['celerydebug'],
            'propagate': True,
        },
        'bibleverses.services': {
            'level': 'INFO',
            'handlers': ['bibleservices'],
            'propagate': True,
        },
        'bibleverses.suggestions': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}


if (DEBUG or TESTING or any(a in sys.argv for a in ['setup_bibleverse_suggestions',
                                                    'run_suggestions_analyzers'])):
    LOGGING['root'] = {
        'level': 'WARNING',
        'handlers': ['console'],
    }
    LOGGING['loggers']['django_ftl.message_errors'] = {
        'level': 'INFO',
        'handlers': ['console'],
        'propagate': False,
    }
else:
    if SENTRY_DSN:
        version = subprocess.check_output(['hg', '--cwd', SRC_ROOT, 'id', '-i']).strip().decode('utf-8')
        release = "learnscripturenet@" + version
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration(), CeleryIntegration()],
            release=release,
        )

if TESTING:
    LOGGING['handlers']['console']['level'] = 'ERROR'

SILENCED_SYSTEM_CHECKS = [
    "1_6.W001",
]

CMS_DEFAULT_TEMPLATE = 'cms_singlecol.html'
CMS_TEMPLATE_CHOICES = [(CMS_DEFAULT_TEMPLATE, 'Single column')]


def show_toolbar(request):
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    from django.conf import settings
    if request.META.get('REMOTE_ADDR', None) not in settings.INTERNAL_IPS:
        return False

    if request.path.startswith('/static'):
        return False

    if request.path.startswith('/learn'):
        return False

    return bool(settings.DEBUG)


DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': set(['debug_toolbar.panels.redirects.RedirectsPanel']),
    'JQUERY_URL': '',
    'SHOW_TOOLBAR_CALLBACK': 'learnscripture.settings.show_toolbar',
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': f'unix:{HOME_DIR}/learnscripture_memcached.sock',
        'KEY_PREFIX': 'learnscripture.net',
    }
} if LIVEBOX else {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
} if TESTING else {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    'raw_enabled': False,
    'file_insertion_enabled': False,
    'embed_stylesheet': False,
    'stylesheet': None,
}

MARKUP_SETTINGS = {
    'restructuredtext': {
        'settings_overrides': RESTRUCTUREDTEXT_FILTER_SETTINGS,
    }
}

CAMPAIGN_CONTEXT_PROCESSORS = [
    'learnscripture.context_processors.campaign_context_processor'
]


# Celery

CELERY_BROKER_URL = 'amqp://{0}:{1}@localhost:5672/learnscripture'.format(secrets['RABBITMQ_USERNAME'],
                                                                          secrets['RABBITMQ_PASSWORD'])

# For easier debugging, we run Celery tasks in main process
# when in development.
if TESTING or DEVBOX:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
else:
    CELERY_TASK_ALWAYS_EAGER = False
    CELERY_TASK_EAGER_PROPAGATES = False

CELERY_WORKER_CONCURRENCY = 2
CELERY_WORKER_PREFETCH_MULTIPLIER = 64

CELERY_RESULT_BACKEND = 'disabled'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_IGNORE_RESULT = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# Webpack

if DEVBOX:
    if TESTING:
        WEBPACK_STATS_FILE = 'webpack-stats.tests.json'
    else:
        WEBPACK_STATS_FILE = 'webpack-stats.dev.json'
else:
    WEBPACK_STATS_FILE = 'webpack-stats.deploy.json'

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG or TESTING,
        'BUNDLE_DIR_NAME': 'webpack_bundles/',
        'STATS_FILE': os.path.join(SRC_ROOT, WEBPACK_STATS_FILE),
        'POLL_INTERVAL': 0.1,
        'TIMEOUT': None,
        'IGNORE': [r'.+\.hot-update.js', r'.+\.map']
    }
}

# == LearnScripture.net specific settings ==

IDENTITY_EXPIRES_DAYS = 22

MINIMUM_PASSWORD_LENGTH = 6

REQUIRE_SUBSCRIPTION = False

ESV_API_KEY = secrets['ESV_API_KEY']

if TESTING:
    import faulthandler
    import signal
    faulthandler.enable()

    # If the process receives signal SIGUSR1, dump a traceback
    faulthandler.register(signal.SIGUSR1)


if DEBUG:
    try:
        from sqlparse import format as sqlformat
    except ImportError:
        sqlformat = lambda s, reindent=None: s
    from traceback import format_stack

    class SqlWithStacktrace(object):
        def __init__(self, skip=[], limit=5):
            self.skip = [__name__, 'logging']
            self.skip.extend(skip)
            self.limit = limit

        def filter(self, record):
            if not hasattr(record, 'stack_patched'):
                frame = sys._getframe(1)
                if self.skip:
                    while [skip for skip in self.skip if frame.f_globals.get('__name__', '').startswith(skip)]:
                        frame = frame.f_back
                if hasattr(record, 'duration') and hasattr(record, 'sql') and hasattr(record, 'params'):
                    record.msg = "\nFrom stack: \n\x1b[32m%s\x1b[0m\n \x1b[31mduration: %s%.4f secs\x1b[0m, \x1b[33marguments: %s%s\x1b[0m\n  \x1b[1;33m%s\x1b[0m\n" % (
                        ''.join(format_stack(f=frame, limit=self.limit)).rstrip(),
                        "\x1b[31m" if record.duration < 0.1 else "\x1b[1;31m", record.duration,
                        "\x1b[1;33m" if record.params else '', record.params,
                        '\n  '.join(sqlformat(record.sql, reindent=True).strip().splitlines()),
                    )
                else:
                    record.msg += "\n -- stack: \n\x1b[32m%s\x1b[0m" % (
                        ''.join(format_stack(f=frame, limit=self.limit)).rstrip()
                    )
                record.stack_patched = True
            return True

    LOGGING.setdefault('filters', {})['add_sql_with_stack'] = {
        '()': SqlWithStacktrace,
        'skip': ("django.db", "django.contrib", "__main__"),
        'limit': 3,  # increase this if not enough
    }

    # To add DB debugging, uncomment this:
    # LOGGING['loggers']['django.db.backends'] = {
    #     'level': 'DEBUG',
    #     'filters': ['add_sql_with_stack'],
    # }

if DEBUG:
    # Delete all but 20 most recent entries, to keep things trim
    for f in sorted(glob.glob("./learnscripture/static/webpack_bundles/*.dev.*"),
                    reverse=True,
                    key=os.path.getctime)[20:]:
        os.unlink(f)

if TESTING:
    # Monkey patch WebpackLoader to call `webpack` just in time.
    # This means that tests that don't need to run webpack
    # don't have that overhead.
    from webpack_loader.loader import WebpackLoader

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
