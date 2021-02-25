import os
from yaml import safe_load as load_yaml
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILE_PATH = os.environ.get('CONFIG_FILE', 'config.yaml')
CONFIG_DICT = None
with open(CONFIG_FILE_PATH, 'r') as f:
    CONFIG_DICT = load_yaml(f)


SECRET_KEY = CONFIG_DICT['web']['secret-key']

DEBUG = CONFIG_DICT['web']['debug']

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'drive.apps.DriveConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django.contrib.admin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]

if not DEBUG:
    MIDDLEWARE.append('django.middleware.csrf.CsrfViewMiddleware')

ROOT_URLCONF = 'rpidrive.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'rpidrive.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {}
DB_ENGINE = CONFIG_DICT['database']['engine']
if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES['default'] = {
        'ENGINE': DB_ENGINE,
        'NAME': CONFIG_DICT['database']['name'],
    }
elif DB_ENGINE == 'django.db.backends.postgresql_psycopg2':
    DATABASES['default'] = {
        'ENGINE': DB_ENGINE,
        'HOST': CONFIG_DICT['database']['host'],
        'PORT': CONFIG_DICT['database']['port'],
        'NAME': CONFIG_DICT['database']['name'],
        'USER': CONFIG_DICT['database']['user'],
        'PASSWORD': CONFIG_DICT['database']['password'],
        'CONN_MAX_AGE': 300,
    }
else:
    raise Exception('Invalid db engine!')

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = CONFIG_DICT['web']['time-zone']

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

REVERSE_PROXY_IP_HEADER = CONFIG_DICT['reverse-proxy']['ip-header']

REDIS = CONFIG_DICT['redis']
REDIS_HOST = REDIS['host']
REDIS_PORT = REDIS['port']
REDIS_DB = REDIS['db']

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': '{}:{}'.format(REDIS_HOST, REDIS_PORT)
    }
}

LOGIN_MAX_RETRIES = CONFIG_DICT['security']['login-protect']['max-retries']
LOGIN_BLOCK_DURATION = CONFIG_DICT['security']['login-protect']['block-duration']

INDEXER_PERIOD = CONFIG_DICT['indexer']['period']

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_URL = '/drive/static/'

_TEMP_DIR = CONFIG_DICT['web'].get('temp-dir', None)
if _TEMP_DIR:
    FILE_UPLOAD_TEMP_DIR = os.path.join(_TEMP_DIR, 'uploads')
    if not os.path.exists(FILE_UPLOAD_TEMP_DIR):
        os.makedirs(FILE_UPLOAD_TEMP_DIR)

"""
if DEBUG:
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
            'django': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
"""