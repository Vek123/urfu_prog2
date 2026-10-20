import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
from math import isfinite

from django.core.exceptions import ImproperlyConfigured
from environ import Env

BASE_DIR = Path(__file__).resolve().parent

env = Env()
env.read_env(BASE_DIR.parent / ".env")

sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

SECRET_KEY = env.str("SECRET_KEY")

DEBUG = env.bool("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.hello',
    'apps.feedback',
    'apps.education',
]

MIDDLEWARE = [
    'apps.education.monitoring.RequestMetricsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-RU'

LANGUAGES = [
    ("ru", "Russian"),
    ("en", "English")
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [
    "locale",
]

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

FEEDBACK_RESPONSE_MODIFIER = env.str(
    'FEEDBACK_RESPONSE_MODIFIER', default='systemTime')
if FEEDBACK_RESPONSE_MODIFIER not in ('systemTime', 'operationUid'):
    raise ImproperlyConfigured(
        'FEEDBACK_RESPONSE_MODIFIER must be systemTime or operationUid')

FEEDBACK_SERVICE_NAME = 'Service 1'
FEEDBACK_FORWARD_REQUESTS = True
FEEDBACK_ALLOW_SERVICE_SYSTEM = False
SERVICE2_URL = env.str('SERVICE2_URL', default='http://127.0.0.1:8084/feedback')
SERVICE2_TIMEOUT = env.float('SERVICE2_TIMEOUT', default=5.0)
if not isfinite(SERVICE2_TIMEOUT) or SERVICE2_TIMEOUT <= 0:
    raise ImproperlyConfigured('SERVICE2_TIMEOUT must be a positive finite number')
if urlsplit(SERVICE2_URL).scheme not in ('http', 'https') or not urlsplit(SERVICE2_URL).netloc:
    raise ImproperlyConfigured('SERVICE2_URL must be an absolute HTTP(S) URL')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': ('{asctime} {levelname} ' + FEEDBACK_SERVICE_NAME
                       + ' {name} {message}'),
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'apps.feedback': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
