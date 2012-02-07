# Django settings for learnscripture project.

import socket
import os


hostname = socket.gethostname()
DEVBOX = ('webfaction' not in hostname)
LIVEBOX = not DEVBOX
DEBUG = DEVBOX
TEMPLATE_DEBUG = DEBUG

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # ../
PROJECT_DIR = os.path.dirname(SRC_DIR)
WEBAPP_DIR = os.path.dirname(PROJECT_DIR)

from .settings_priv import SECRET_KEY
if LIVEBOX:
    from .settings_priv import DATABASES, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'learnscripture',
            'USER': 'learnscripture',
            'PASSWORD': 'foo',
            'HOST': '',
            'PORT': '',
        }
    }

ADMINS = [
    ('', 'admin@learnscripture.net')
]

MANAGERS = ADMINS

if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

SERVER_EMAIL = 'website@learnscripture.net'
DEFAULT_FROM_EMAIL = SERVER_EMAIL

TIME_ZONE = 'Europe/London'
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

USE_I18N = False
USE_L10N = False
USE_TZ = True

if LIVEBOX:
    MEDIA_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_usermedia')
    STATIC_ROOT = os.path.join(WEBAPP_DIR, 'learnscripture_static')
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

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = [
    m for b, m in
    [
        (True, 'django.middleware.common.CommonMiddleware'),
        (True, 'django.contrib.sessions.middleware.SessionMiddleware'),
        (True, 'django.middleware.csrf.CsrfViewMiddleware'),
        (True, 'django.contrib.auth.middleware.AuthenticationMiddleware'),
        (True, 'django.contrib.messages.middleware.MessageMiddleware'),
        (True, 'django.middleware.clickjacking.XFrameOptionsMiddleware'),
        (True, 'learnscripture.middleware.IdentityMiddleware'),
        (True, 'pagination.middleware.PaginationMiddleware'),
        (True, 'raven.contrib.django.middleware.Sentry404CatchMiddleware'),
        (DEBUG, 'debug_toolbar.middleware.DebugToolbarMiddleware'),
    ]
    if b
]


TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'fiber.context_processors.page_info',
    'learnscripture.context_processors.session_forms',
    'learnscripture.context_processors.menu',
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
    'south',
    'learnscripture',
    'bibleverses',
    'accounts',
    'piston',
    'mptt',
    'compressor',
    'fiber',
    'bootstrapform',
    'pagination',
    'raven.contrib.django',
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
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'unix:/home/cciw/memcached.sock',
        'KEY_PREFIX': 'learnscripture.net',
    }
}


COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

# We don't want CssAbsoluteFilter because it adds ?randomdigits to URLs, and
# some browsers (e.g. mine) decide not to cache the result.
COMPRESS_CSS_FILTERS = []

### Sentry/Raven ###

from settings_priv import SENTRY_DSN

SENTRY_CLIENT = 'ravenclient.AsyncDjangoClient'

### LearnScripture.net specific settings ###

IDENTITY_EXPIRES_DAYS = 21

MINIMUM_PASSWORD_LENGTH = 6


