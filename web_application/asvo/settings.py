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
import os, logging, datetime
from django.core.urlresolvers import reverse

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
    'astrospark',
    'authentication',
    'bootstrap3',
    'corsheaders',
    'documentation',
    'django_extensions',
    'hitcount',
    'feature',
    'mathfilters',
    'query',
    'user',
    'restapi_app',
    # 'rest_framework.authtoken',
    'rest_framework',
    'schema_browser',
    'sov',
    'surveys',
    'vote',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'asvo.middleware.SleepMiddleware'
)

SLEEP_TIME = 1
# TODO turn SleepMiddleware off in production!

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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # default
)

LOGIN_REDIRECT_URL = 'index'
LOGIN_URL = 'rest_framework:login'

WSGI_APPLICATION = 'asvo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
# DEVELOPMENT SQLite:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# PRODUCTION PostgreSQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'aaodc',
#         # 'NAME': os.path.join(BASE_DIR, 'db.postgresql_psycopg2'),
#         'USER': 'root',
#         # 'PASSWORD': '',
#         # 'HOST': '127.0.0.1',
#         # 'PORT': '8000',
#     }
# }



CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

# TURN THIS OFF IN PRODUCTION! Dumps email in console for testing
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'comsrv.aao.gov.au'
EMAIL_PORT = 25

# spark
SPARK_HOME = '/Applications/spark-1.5.0-bin-hadoop2.6/'
SPARK_PATH = ['/Applications/spark-1.5.0-bin-hadoop2.6/python']

# SAMI Database:
#
#    Set these to the location of the SAMI database directory and corresponding
#    catalog file.
SAMI_TEAM_DATABASE = ''
SAMI_TEAM_DATABASE_CATALOG = ''

SAMI_DR1_DATABASE = ''
SAMI_DR1_DATABASE_CATALOG = ''


# Pandoc paths
# https://pypi.python.org/pypi/pypandoc
PANDOC_PATH = '/usr/bin/pandoc'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-AU'

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


# MEDIA_URL = '/media/'
# MEDIA_ROOT = (
#     os.path.join(BASE_DIR, "media_root"), '/var/www/media/',)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


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
            'level': 'WARNING',
            'class': 'logging.NullHandler',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.dirname(__file__) + '/aatnode-django.log',
            'formatter': 'verbose_with_times'
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            # 'filters': ['debug_filter']
        }
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'filters': ['special']
        # }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'propagate': True,
            'level': 'WARNING',
        },
        # 'django.request': {
        #     'handlers': ['mail_admins'],
        #     'level': 'ERROR',
        #     'propagate': False,
        # },
        'aatnode': {
            'handlers': ['console', 'file'],
            'level': 'WARNING'
        },
        'restapi_app': {
            'handlers': ['console', 'file'],
            'level': 'WARNING'
        },
        'sov': {
            'handlers': ['console', 'file'],
            'level': 'WARNING'
        },
        'fidia': {
            'handlers': ['console', 'file'],
            'level': 'WARNING'
        }
    }
}

try:
    from .custom_settings import *
except ImportError:
    pass

# Bring pandoc path into effect.
os.environ.setdefault('PYPANDOC_PANDOC', PANDOC_PATH)


REST_FRAMEWORK = {
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
    ),
     'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.TokenAuthentication',
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '5/day',
    },
    'TEST_REQUEST_RENDERER_CLASSES': (
        'rest_framework.renderers.MultiPartRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.TemplateHTMLRenderer',
        # 'restapi_app.renderers_custom.renderer_flat_csv.FlatCSVRenderer'
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    # 'EXCEPTION_HANDLER': 'restapi_app.utils..exceptions.custom_exception_handler'
}


CORS_ORIGIN_WHITELIST = (
    # 'google.com.au',
    'localhost:3000',
    'localhost:8000',
    '127.0.0.1:9000'
)

# token expires in 12 hours
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=43200),
}

CSRF_COOKIE_NAME = "XSRF-TOKEN"
