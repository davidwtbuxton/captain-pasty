import os

from djangae import environment
from djangae.settings_base import *

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
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'pasty.middleware.GoogleUserMiddleware',
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


WSGI_APPLICATION = 'project.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = False
USE_TZ = True

STATIC_URL = '/static/'

DEFAULT_FILE_STORAGE = 'djangae.storage.CloudStorage'
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 5
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
)

# The '{host}' shortcut is handled by pasty.middleware.CSPHostnameMiddleware.
CSP_DEFAULT_SRC = ["'none'"]
CSP_STYLE_SRC = ['{host}/static/styles.css']
CSP_SCRIPT_SRC = ['{host}/static/app.min.js', '{host}/static/src/']
CSP_IMG_SRC = ['{host}/static/pic/', '{host}/favicon.ico']
CSP_FONT_SRC = ['{host}/static/fonts/']
