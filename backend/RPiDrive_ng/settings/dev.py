SECRET_KEY = 'fncxsng(81-$ruzd$h-w3v8f-qj)2e)u*$w+f&!c!)7mx62^oq'
DEBUG = True
ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'rpidrive',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '192.168.0.182',
        'PORT': '5432',
    }
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ARIA2_HOST = '192.168.0.182'
ARIA2_PORT = '6800'
ARIA2_SECRET = 'rpidrive'

from .settings import *

INSTALLED_APPS += ['corsheaders']
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True