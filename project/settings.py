import os

from djangae import environment
# from djangae.settings_base import *

from .boot import AppConfig


ON_PROD = environment.is_production_environment()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = AppConfig.get().secret_key
DEBUG = not ON_PROD
INTERNAL_IPS = ('127.0.0.1', '::1')

INSTALLED_APPS = [
    'djangae',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pasty',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'session_csrf.CsrfMiddleware',
    'pasty.middleware.GoogleUserMiddleware',
    'pasty.middleware.PastyVersionMiddleware',
    'pasty.middleware.CSPHostnameMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'session_csrf.context_processor',
                'pasty.context_processors.pasty',
            ],
            'loaders': ['django.template.loaders.app_directories.Loader'],
            # So templates don't have to {% load %} anything.
            'builtins': ['pasty.templatetags.pastytags'],
        },
    },
]

# Enable template caching in production.
if not DEBUG:
    opts = TEMPLATES[0]['OPTIONS']
    opts['loaders'] = [('django.template.loaders.cached.Loader', opts['loaders'])]

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

WSGI_APPLICATION = 'project.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = False
USE_TZ = True

STATIC_URL = '/static/'

# The '{host}' shortcut is handled by pasty.middleware.CSPHostnameMiddleware.
CSP_DEFAULT_SRC = ["'none'"]
CSP_CONNECT_SRC = ['{host}/api/v1/']
CSP_STYLE_SRC = ['{host}/static/styles.css']
CSP_SCRIPT_SRC = ['{host}/static/app.min.js', '{host}/static/src/']
CSP_IMG_SRC = ['{host}/static/pic/', '{host}/favicon.ico']
CSP_FONT_SRC = ['{host}/static/fonts/']

# Results per page.
PAGE_SIZE = 10

DATABASES = {
    'default': {'ENGINE': 'djangae.db.backends.appengine'},
}

EMAIL_BACKEND = 'djangae.mail.AsyncEmailBackend'

ALLOWED_HOSTS = ('*',)

FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'djangae': {
            'level': 'WARN',
        },
    },
}

# Allow anonymous users to post things.
ANON_ALWAYS = True

DJANGAE_RUNSERVER_IGNORED_DIR_REGEXES = [r'^libs$']
