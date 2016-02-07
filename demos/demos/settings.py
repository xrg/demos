# -*- encoding: utf-8 -*-
# File: base.py

"""
Django settings for demos project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = NO_SECRET_KEY_DEFINED

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
DEVELOPMENT = False      # would turn off security, enable DEBUG

ALLOWED_HOSTS = [
    '',
]

ADMINS = [
    ('Root', 'root@localhost'),
]


# All writable files may have this as a reference

SPOOL_DIR = '/var/spool/demos-voting'

if DEVELOPMENT:
    SPOOL_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    ]

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    ]

ROOT_URLCONF = 'demos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'common/templates')
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'demos.common.utils.context_processors.common',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

WSGI_APPLICATION = 'demos.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'demos_voting',
        'USER': 'demos_voting',
        #'PASSWORD': '',
        #'HOST': '',
        #'PORT': '',
    }
}

BROKER_URL = 'amqp://'
CELERY_RESULT_BACKEND = 'amqp'
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_ACCEPT_CONTENT = ['json', 'msgpack']

if DEVELOPMENT:
    # Alternative config, only using Django + existing db
    # Note: introduces dependency on python-SQLAlchemy
    BROKER_URL = 'django://'
    INSTALLED_APPS.append('kombu.transport.django')
    CELERY_RESULT_BACKEND='db+postgresql://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s/%(NAME)s' \
                                % DATABASES['default']


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

from django.utils.translation import ugettext_lazy as _

LANGUAGES = [
    ('el', _('Greek')),
    ('en', _('English')),
]

LANGUAGE_CODE = 'en-us'

USE_TZ = True
TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'common/locale'),
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'common/static'),
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static')


# Sending email
# https://docs.djangoproject.com/en/1.8/topics/email/

EMAIL_HOST = ''
EMAIL_PORT = 587
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = ''
SERVER_EMAIL = ''


# Logging
# https://docs.djangoproject.com/en/1.8/topics/logging/

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log', # Linux-specific
        }
    },
    'loggers': {
        'root': {
            'handlers': ['syslog',]
            },
        'django': {
            'handlers': ['mail_admins', 'syslog'],
            'level': 'INFO',
        },
        'demos': {
            'handlers': ['mail_admins', 'syslog'],
            'level': 'INFO',
        },
        'django_cas': {
             'handlers': ['syslog',],
             'level': 'DEBUG',
            },
    },
}


# Security Middleware
# https://docs.djangoproject.com/en/1.8/ref/middleware/#module-django.middleware.security

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True


# Demos-specific configuration

DEMOS_CONFIG = {

    'ea': {

        # Election configuration
        'MAX_BALLOTS': 100000,
        'MAX_OPTIONS': 128,
        'MAX_TRUSTEES': 128,
        'MAX_QUESTIONS': 32,

        # demos-crypto connection parameters, see:
        # https://docs.python.org/3/library/socket.html
        # CRYPTO_AF: e.g. 'AF_UNIX' or 'AF_INET' or 'AF_INET6'
        # CRYPTO_ADDR: e.g. '/tmp/demos-crypto.sock' or ('127.0.0.1', 8999)
        'CRYPTO_AF': 'AF_UNIX',
        'CRYPTO_ADDR': '/run/demos-voting/demos-crypto.sock',

        # Performance settings, they affect CPU and RAM usage, etc

        'BATCH_SIZE': 128,

        'RECV_MAX': 67108864,   # 64 MB
        'RECV_TIMEOUT': 900,   # 15 mins

        # Certificate Authority (X.509 / RSA) used to sign election ballot receipts
        'CA_CERT_PEM': False, # os.path.expanduser('~/ca/cacert.pem'),
        'CA_PKEY_PEM': False, # os.path.expanduser('~/ca/private/cakey.pem'),
        'CA_PKEY_PASSPHRASE': 'BAD_PASSPHRASE',

    },
    'bds': {

        # Absolute path to the directory that will hold machine-local files
        'FILESYSTEM_ROOT': os.path.join(SPOOL_DIR, 'bds'),
    },

    'abb': {
        
        # Performance settings, they affect CPU and RAM usage, etc
        'BATCH_SIZE': 128,
        
        # Absolute path to the directory that will hold machine-local files
        
        'FILESYSTEM_ROOT': os.path.join(SPOOL_DIR, 'abb'),
    },

    'vbb': {
    },
}

DEMOS_APPS = NO_APP_CHOSEN   # one or more of: ea, bds, abb, vbb

DEMOS_URL = {
    'ea': 'https://demos-ea.our-domain.com',
    'bds': 'https://demos-bds.our-domain.com',
    'abb': 'https://demos-abb.our-domain.com',
    'vbb': 'https://demos-vbb.our-domain.com',
}

DEMOS_API_URL = {
    'ea': 'https://api.demos-ea.our-domain.com',
    'bds': 'https://api.demos-bds.our-domain.com',
    'abb': 'https://api.demos-abb.our-domain.com',
    'vbb': 'https://api.demos-vbb.our-domain.com',
}

# In case the API URLs are SSL-enabled and use self-signed certificates,
# their verification can be disabled to allow requests among servers
# http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification

# DEMOS_API_VERIFY = False        # the default is True


INSTALLED_APPS += [ 'demos.apps.%s' % iapp for iapp in DEMOS_APPS ]
LOCALE_PATHS += tuple([ os.path.join(BASE_DIR, 'apps/%s/locale' % iapp) for iapp in DEMOS_APPS])

if False:
    # use CAS for authentication
    INSTALLED_APPS.append('django_cas')
    MIDDLEWARE_CLASSES.append('django_cas.middleware.CASMiddleware')
    LOGIN_URL = 'cas_login'
    CAS_SERVER_URL = 'https://login-devel.uoa.gr/'
    CAS_SERVER_SSL_VERIFY = False
    CAS_RETRY_LOGIN = False
    # CAS_LOGOUT_COMPLETELY = True
    # CAS_IGNORE_REFERER = True
    # CAS_RENEW = False

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'django_cas.backends.CASBackend',
        )
else:
    LOGIN_URL = 'login'


# End of demos-specific configuration

if DEVELOPMENT:
    DEBUG = True
    
    TEMPLATES[0]['APP_DIRS'] = True
    del TEMPLATES[0]['OPTIONS']['loaders']
    
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'root': {
                'handlers': ['console']
            },
            'django': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
            'django.request': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
            'demos': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'INFO', # Only change that if you are in deep SQL trouble!
                'propagate': False,
            },
        }
    }
    
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_SECONDS = 0

    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False

#eof