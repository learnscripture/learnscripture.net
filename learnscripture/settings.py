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
)

LOGIN_URL = '/admin/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'learnscripture.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'learnscripture.wsgi.application'

TEMPLATE_DIRS = []

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'south',
    'learnscripture',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
