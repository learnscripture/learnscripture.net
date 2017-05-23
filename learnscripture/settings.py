# Django settings for learnscripture project.

import socket
import sys
import os
import json

hostname = socket.gethostname()
CHECK_DEPLOY = 'manage.py check --deploy' in ' '.join(sys.argv)
if CHECK_DEPLOY:
    LIVEBOX = True
    DEVBOX = False
else:
    DEVBOX = ('learnscripture' not in hostname)
    LIVEBOX = not DEVBOX


DEBUG = DEVBOX
TEMPLATE_DEBUG = DEBUG

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
    os.system("mkdir -p %s" % LOG_ROOT)

secrets = json.load(open(os.path.join(SRC_ROOT, "config", "secrets.json")))

# At least some passwords need to be bytes, not unicode objects
secrets = dict([(k, s if not isinstance(s, unicode) else s.encode('ascii')) for k, s in secrets.items()])

MAILGUN_API_KEY = secrets['MAILGUN_API_KEY']
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
    EMAIL_BACKEND = "anymail.backends.mailgun.MailgunBackend"
    ANYMAIL = {
        "MAILGUN_API_KEY": MAILGUN_API_KEY,
    }

else:
    # Development settings:

    # We have problems with wordsuggestions DB connections not being closed in
    # test environment, especially related to the non-default DB it seems,
    # probably a Django bug, so we workaround:
    conn_max_age = 0 if TESTING else 120

    DATABASES = {
        DB_LABEL_DEFAULT: {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'learnscripture',
            'USER': 'learnscripture',
            'PASSWORD': 'foo',
            'HOST': 'localhost',
            'PORT': '5432',
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': conn_max_age,
        },
        DB_LABEL_WORDSUGGESTIONS: {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'learnscripture_wordsuggestions',
            'USER': 'learnscripture',
            'PASSWORD': 'foo',
            'HOST': 'localhost',
            'PORT': '5432',
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
REMINDER_EMAIL = 'reminders@learnscripture.net'


if DEVBOX:
    PAYPAL_RECEIVER_EMAIL = 'paypal_1314646057_biz@cciw.co.uk'
    PAYPAL_TEST = True
else:
    PAYPAL_RECEIVER_EMAIL = "paypal@learnscripture.net"
    PAYPAL_TEST = False
PAYPAL_IMAGE = "https://www.paypalobjects.com/en_US/GB/i/btn/btn_buynowCC_LG.gif"

VALID_RECEIVE_CURRENCY = 'GBP'

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

USE_I18N = False
USE_L10N = False
USE_TZ = True

# Sync with fabfile
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'usermedia')
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
DATA_ROOT = os.path.join(PROJECT_ROOT, 'data')


MEDIA_URL = '/usermedia/'
STATIC_URL = '/static/'

STATICFILES_DIRS = []

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

LOGIN_URL = '/admin/'

CSRF_FAILURE_VIEW = 'learnscripture.views.csrf_failure'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = [
    m for b, m in
    [
        (True, 'django.middleware.security.SecurityMiddleware'),
        (DEBUG, 'debug_toolbar.middleware.DebugToolbarMiddleware'),
        (True, 'django.middleware.common.CommonMiddleware'),
        (True, 'django.contrib.sessions.middleware.SessionMiddleware'),
        (True, 'django.middleware.csrf.CsrfViewMiddleware'),
        (True, 'learnscripture.middleware.TokenLoginMiddleware'),
        (True, 'django.contrib.auth.middleware.AuthenticationMiddleware'),
        (True, 'django.contrib.auth.middleware.SessionAuthenticationMiddleware'),
        (True, 'django.contrib.messages.middleware.MessageMiddleware'),
        (True, 'django.middleware.clickjacking.XFrameOptionsMiddleware'),
        (DEVBOX, 'learnscripture.middleware.DebugMiddleware'),
        (DEBUG, 'learnscripture.middleware.PaypalDebugMiddleware'),
        (True, 'learnscripture.middleware.IdentityMiddleware'),
        (True, 'pagination.middleware.PaginationMiddleware'),
        (True, 'fiber.middleware.AdminPageMiddleware'),
    ]
    if b
]


TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.i18n',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'learnscripture.context_processors.session_forms',
    'learnscripture.context_processors.referral_links',
    'learnscripture.context_processors.menu',
    'learnscripture.context_processors.notices',
    'learnscripture.context_processors.theme_fonts',
    'learnscripture.context_processors.settings_processor',
    'learnscripture.context_processors.request_account',
]

ROOT_URLCONF = 'learnscripture.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'learnscripture.wsgi.application'

INSTALLED_APPS = [
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
    'tracking',
    # Third party
    'mptt',
    'compressor',
    'fiber',
    'bootstrapform',
    'pagination',
    'raven.contrib.django.raven_compat',
    'spurl',
    'paypal.standard.ipn',
    'app_metrics',
    'selectable',
    'django_markup',
    'json_field',
    'anymail',
]

ALLOWED_HOSTS = ["learnscripture.net"]
if DEVBOX:
    ALLOWED_HOSTS.extend([
        ".ngrok.io",
        "learnscripture.local",
    ])

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    INSTALLED_APPS.append('devserver')
    DEVSERVER_MODULES = (
        # 'devserver.modules.sql.SQLRealTimeModule',
        'devserver.modules.sql.SQLSummaryModule',
        # 'devserver.modules.profile.ProfileSummaryModule',

        # Modules not enabled by default
        # 'devserver.modules.ajax.AjaxDumpModule',
        # 'devserver.modules.profile.MemoryUseModule',
        # 'devserver.modules.cache.CacheSummaryModule',
        # 'devserver.modules.profile.LineProfilerModule',
    )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'bibleservices': {
            'level': 'INFO',
            'class': 'cloghandler.ConcurrentRotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_ROOT, 'bibleservices_debug.log'),
            'maxBytes': 1024 * 1024,
            'backupCount': 10,
        },
        'celerydebug': {
            'level': 'DEBUG',
            'class': 'cloghandler.ConcurrentRotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_ROOT, 'celery_debug.log'),
            'maxBytes': 1024 * 1024,
            'backupCount': 10,
        },

    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'celery': {
            'level': 'DEBUG',
            'handlers': ['celerydebug', 'sentry'],
            'propagate': False,
        },
        'celerydebug': {
            'level': 'DEBUG',
            'handlers': ['celerydebug'],
            'propagate': False,
        },
        'bibleverses.services': {
            'level': 'INFO',
            'handlers': ['bibleservices'],
            'propagate': False,
        },
    },
}

if DEBUG or 'setup_bibleverse_suggestions' in sys.argv:
    LOGGING['root']['handlers'] = ['console']
    LOGGING['loggers']['celery']['handlers'] = ['console']
    LOGGING['loggers']['bibleverses.suggestions'] = {
        'level': 'INFO',
        'handlers': ['console'],
        'propagate': False,
    }
    LOGGING['loggers']['bibleverses.services'] = {
        'level': 'INFO',
        'handlers': ['console'],
        'propagate': False,
    }


if TESTING:
    LOGGING['handlers']['console']['level'] = 'ERROR'

SILENCED_SYSTEM_CHECKS = [
    "1_6.W001",
]

FIBER_DEFAULT_TEMPLATE = 'fiber_singlecol.html'
FIBER_TEMPLATE_CHOICES = [(FIBER_DEFAULT_TEMPLATE, 'Single column')]

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'unix:%s/learnscripture_memcached.sock' % HOME_DIR,
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

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    'raw_enabled': False,
    'file_insertion_enabled': False,
}

MARKUP_SETTINGS = {
    'restructuredtext': {
        'settings_overrides': RESTRUCTUREDTEXT_FILTER_SETTINGS,
    }
}

CAMPAIGN_CONTEXT_PROCESSORS = [
    'learnscripture.context_processors.campaign_context_processor'
]


# Raven

if DEBUG:
    RAVEN_CONFIG = {}
    SENTRY_DSN = None
    SENTRY_KEY = None
else:
    RAVEN_CONFIG = {
        'dsn': SENTRY_DSN,
    }


# Celery

if LIVEBOX:
    CELERY_BROKER_URL = 'amqp://{0}:{1}@localhost:5672//'.format(secrets['RABBITMQ_USERNAME'],
                                                                 secrets['RABBITMQ_PASSWORD'])
else:
    CELERY_BROKER_URL = 'amqp://{0}:{1}@localhost:5672//'.format('learnscripture',
                                                                 'foo')

# For easier debugging, we run Celery tasks in main process
# when in development.
if TESTING or DEVBOX:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 64

CELERY_RESULT_BACKEND = 'disabled'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_IGNORE_RESULT = True
CELERY_WORKER_HIJACK_ROOT_LOGGER = False

# == LearnScripture.net specific settings ==

IDENTITY_EXPIRES_DAYS = 22

MINIMUM_PASSWORD_LENGTH = 6

REQUIRE_SUBSCRIPTION = False

if LIVEBOX:
    ESV_API_KEY = secrets['ESV_API_KEY']
else:
    ESV_API_KEY = 'IP'

if LIVEBOX:
    GOOGLE_ANALYTICS_ACCOUNT = "UA-29644888-1"
else:
    GOOGLE_ANALYTICS_ACCOUNT = None


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
