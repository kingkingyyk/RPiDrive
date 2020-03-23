from .settings import *

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

ARIA2_HOST = '192.168.0.182'
ARIA2_PORT = '6800'
ARIA2_SECRET = 'rpidrive'