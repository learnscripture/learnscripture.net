# Django settings for learnscripture project.

import socket
import sys
import os
import simplejson

hostname = socket.gethostname()
DEVBOX = ('webfaction' not in hostname)
LIVEBOX = not DEVBOX
DEBUG = DEVBOX
TEMPLATE_DEBUG = DEBUG

# A kitten gets killed every time you use this:
TESTING = 'manage.py test' in ' '.join(sys.argv)

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ../
PROJECT_DIR = os.path.dirname(SRC_DIR)
WEBAPP_DIR = os.path.dirname(PROJECT_DIR)
HOME_DIR = os.environ['HOME']

secrets = simplejson.load(open(os.path.join(SRC_DIR, "config", "secrets.json")))


if LIVEBOX:
    p = os.path.dirname(os.path.abspath(__file__))
    PRODUCTION = "webapps/learnscripture_django/" in p
    STAGING = "webapps/learnscripture_staging_django/" in p

    assert not (PRODUCTION and STAGING)

    EMAIL_HOST = secrets['EMAIL_HOST']
    EMAIL_HOST_USER = secrets['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD = secrets['EMAIL_HOST_PASSWORD']

    if PRODUCTION:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': secrets["LEARNSCRIPTURE_DB_NAME"],
                'USER': secrets["LEARNSCRIPTURE_DB_USER"],
                'PASSWORD': secrets["LEARNSCRIPTURE_DB_PASSWORD"],
                'HOST': 'localhost',
                'PORT': secrets["LEARNSCRIPTURE_DB_PORT"],
                }
            }
        SECRET_KEY = secrets["PRODUCTION_SECRET_KEY"]
        SENTRY_DSN = secrets["PRODUCTION_SENTRY_DSN"]

    elif STAGING:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': secrets["LEARNSCRIPTURE_STAGING_DB_NAME"],
                'USER': secrets["LEARNSCRIPTURE_STAGING_DB_USER"],
                'PASSWORD': secrets["LEARNSCRIPTURE_STAGING_DB_PASSWORD"],
                'HOST': 'localhost',
                'PORT': secrets["LEARNSCRIPTURE_STAGING_DB_PORT"],
                }
            }
        SECRET_KEY = secrets["STAGING_SECRET_KEY"]
        SENTRY_DSN = secrets["STAGING_SENTRY_DSN"]
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'learnscripture',
            'USER': 'learnscripture',
            'PASSWORD': 'foo',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

    # For e-mail testing, run:
    #  fakemail.py --path=/home/luke/devel/learnscripture.net/tests/mail --background
    EMAIL_HOST = 'localhost'
    EMAIL_HOST_USER = None
    EMAIL_HOST_PASSWORD = None
    EMAIL_PORT = 8025

    SECRET_KEY = secrets['DEVELOPMENT_SECRET_KEY']
    SENTRY_DSN = secrets["DEVELOPMENT_SENTRY_DSN"]


SESSION_COOKIE_AGE = 3600 * 24 * 31 * 4 # 4 months

ADMINS = [
    ('', 'admin@learnscripture.net')
]

MANAGERS = ADMINS

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

SERVER_EMAIL = 'website@learnscripture.net'
DEFAULT_FROM_EMAIL = 'luke@learnscripture.net'


if DEVBOX or STAGING:
    PAYPAL_RECEIVER_EMAIL = 'paypal_1314646057_biz@cciw.co.uk'
    PAYPAL_TEST = True
else:
    PAYPAL_RECEIVER_EMAIL = "paypal@learnscripture.net"
    PAYPAL_TEST = False
PAYPAL_IMAGE = "https://www.paypalobjects.com/en_US/GB/i/btn/btn_buynowCC_LG.gif"


TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

USE_I18N = False
USE_L10N = False
USE_TZ = True

if LIVEBOX:
    if PRODUCTION:
        MEDIA_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_usermedia')
        STATIC_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_static')
    elif STAGING:
        MEDIA_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_staging_usermedia')
        STATIC_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_staging_static')

else:
    MEDIA_ROOT = os.path.join(PROJECT_DIR, 'usermedia')
    STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

MEDIA_URL = '/usermedia/'
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'


STATICFILES_DIRS = []

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

LOGIN_URL = '/admin/'

CSRF_FAILURE_VIEW = 'learnscripture.views.csrf_failure'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = [
    m for b, m in
    [
        (DEBUG, 'debug_toolbar.middleware.DebugToolbarMiddleware'),
        (True, 'learnscripture.middleware.StatsMiddleware'),
        (True, 'django.middleware.common.CommonMiddleware'),
        (True, 'django.middleware.transaction.TransactionMiddleware'),
        (True, 'django.contrib.sessions.middleware.SessionMiddleware'),
        (True, 'django.middleware.csrf.CsrfViewMiddleware'),
        (True, 'django.contrib.auth.middleware.AuthenticationMiddleware'),
        (True, 'django.contrib.messages.middleware.MessageMiddleware'),
        (True, 'django.middleware.clickjacking.XFrameOptionsMiddleware'),
        (DEVBOX, 'learnscripture.middleware.DebugMiddleware'),
        (True, 'learnscripture.middleware.IdentityMiddleware'),
        (True, 'pagination.middleware.PaginationMiddleware'),
        (True, 'raven.contrib.django.middleware.Sentry404CatchMiddleware'),
        (not DEBUG, 'fiber.middleware.AdminPageMiddleware'),
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
    'learnscripture.context_processors.lazy_page_info',
    'learnscripture.context_processors.session_forms',
    'learnscripture.context_processors.referral_links',
    'learnscripture.context_processors.menu',
    'learnscripture.context_processors.notices',
]

ROOT_URLCONF = 'learnscripture.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'learnscripture.wsgi.application'

TEMPLATE_DIRS = []

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.markup',
    'django.contrib.humanize',
    'south',
    # This project
    'learnscripture',
    'bibleverses',
    'accounts',
    'scores',
    'payments',
    'awards',
    'events',
    'groups',
    # Third party
    'piston',
    'mptt',
    'compressor',
    'fiber',
    'bootstrapform',
    'pagination',
    'raven.contrib.django',
    'spurl',
    'paypal.standard.ipn',
    'campaign',
    'djcelery',
    'app_metrics',
    'selectable',
]

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')


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
            'level': 'INFO',
            'class': 'raven.contrib.django.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'learnscripture': {
            'level': 'INFO',
            'handlers': ['sentry'],
            'propagate': False,
            },
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
            'level': 'WARNING',
            'handlers': ['sentry'],
            'propagate': False,
        },
    },
}

FIBER_DEFAULT_TEMPLATE = 'fiber_singlecol.html'
FIBER_TEMPLATE_CHOICES = [(FIBER_DEFAULT_TEMPLATE, 'Single column')]



PISTON_DISPLAY_ERRORS = False


DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    }

CACHES = {
    'default': {
        'BACKEND': 'caching.backends.memcached.CacheClass',
        'LOCATION': 'unix:%s/memcached.sock' % HOME_DIR,
        'KEY_PREFIX': 'learnscripture.net' if PRODUCTION else 'staging.learnscripture.net'
    }
} if LIVEBOX else {}

CACHE_PREFIX = 'ls1'

if 'test' in sys.argv:
    # Caching count() seems to cause errors in test suite
    CACHE_COUNT_TIMEOUT = 0
else:
    CACHE_COUNT_TIMEOUT = 60

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    'raw_enabled': False,
    'file_insertion_enabled': False,
}

CAMPAIGN_CONTEXT_PROCESSORS = [
    'learnscripture.context_processors.campaign_context_processor'
]

### Celery and RabbitMQ ###

import djcelery
djcelery.setup_loader()

if LIVEBOX:
    if PRODUCTION:
        rabbitmq_user = "learnscripture"
        rabbitmq_pass = secrets["PRODUCTION_RABBITMQ_PASSWORD"]
        rabbitmq_port = 32048 # see also rabbitmq-env
    if STAGING:
        rabbitmq_user = "learnscripture_staging"
        rabbitmq_pass = secrets["STAGING_RABBITMQ_PASSWORD"]
        rabbitmq_port = 47292

if DEVBOX:
    rabbitmq_user = "learnscripture"
    rabbitmq_pass = "foo"
    rabbitmq_port = 32048
rabbitmq_vhost = rabbitmq_user

BROKER_URL = "amqp://%s:%s@localhost:%s/%s" % (rabbitmq_user, rabbitmq_pass, rabbitmq_port, rabbitmq_vhost)

if TESTING or DEVBOX:
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

CELERYD_CONCURRENCY = 1

### Sentry/Raven ###

SENTRY_CLIENT = 'ravenclient.AsyncDjangoClient'

### LearnScripture.net specific settings ###

IDENTITY_EXPIRES_DAYS = 22

MINIMUM_PASSWORD_LENGTH = 6

REQUIRE_SUBSCRIPTION = True

