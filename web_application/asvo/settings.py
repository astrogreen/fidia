"""
Django settings for asvo project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/

NOTE: This file contains generic settings for use e.g. on the production
server. If you want to override any settings here e.g. for your local copy,
create a new (unversioned) file "custom_settings.py" in this directory and
put the overrides there. They are loaded at the end of this file.

"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.core.urlresolvers import reverse
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '_(19ic0&_y2fuld((%jwmz@=*%ejz6*24*0foua)l*v2s^q+k!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'aatnode',
    'astrospark',
    'bootstrap3',
    # 'captcha',
    # 'clever_selects',
    'django_extensions',
    'mathfilters',
    'restapi_app',
    'rest_framework',
    'rest_framework.authtoken',
    # 'rest_framework_swagger',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'asvo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'aatnode/templates/aatnode/').replace('\\','/'),],
        # 'DIRS': [os.path.join(BASE_DIR, 'templates').replace('\\','/'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGIN_REDIRECT_URL = 'index'

WSGI_APPLICATION = 'asvo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Spark

# spark
SPARK_HOME = '/Applications/spark-1.5.0-bin-hadoop2.6/'
SPARK_PATH = ['/Applications/spark-1.5.0-bin-hadoop2.6/python']

# SAMI Database:
#
#    Set these to the location of the SAMI database directory and corresponding
#    catalog file.
SAMI_TEAM_DATABASE = ''
SAMI_TEAM_DATABASE_CATALOG = ''


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Australia/Sydney'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
    '/var/www/static/',
)


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media_root")

# Query results cache

CACHE_DIR = '/tmp/asvo_cache/'

class DebugLogFilter:
    def filter(self, record):
        assert isinstance(record, logging.LogRecord)
        emitting_logger = logging.getLogger(record.name)
        return (record.levelno >= emitting_logger.level and
                emitting_logger.level != logging.NOTSET) or record.levelno >= logging.WARNING


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(filename)s:%(lineno)s %(funcName)s: %(message)s'
        },
        'verbose_with_times': {
            'format': '%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(funcName)s: %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'debug_filter': {
            '()': DebugLogFilter,
        },
    },
    # 'filters': {
    #     'special': {
    #         '()': 'project.logging.SpecialFilter',
    #         'foo': 'bar',
    #     }
    # },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.dirname(__file__) + '/aatnode-django.log',
            'formatter': 'verbose_with_times'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['debug_filter']
        }
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'filters': ['special']
        # }
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'INFO',
        },
        # 'django.request': {
        #     'handlers': ['mail_admins'],
        #     'level': 'ERROR',
        #     'propagate': False,
        # },
        'aatnode': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG'
        },
        'restapi_app': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG'
        },
        'fidia': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG'
        }
    }
}

try:
    from .custom_settings import *
except ImportError:
    pass


RECAPTCHA_PUBLIC_KEY = '6LdTGw8TAAAAACaJN7aHD44SVDccIWE-ssIzEQ4j'
RECAPTCHA_PRIVATE_KEY = '6LdTGw8TAAAAAGSIcSt4BdOpedOmWcihBLZdL3qn'
NOCAPTCHA = True

REST_FRAMEWORK = {
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
     'DEFAULT_AUTHENTICATION_CLASSES': (
        # 'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}
