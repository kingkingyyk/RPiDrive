from .settings import *
import os

OS_EVARS = ['SECRET_KEY', 'DB_USER', 'DB_PASSWORD', 'DB_HOST',
            'DB_PORT', 'ARIA2_HOST', 'ARIA2_PORT', 'ARIA2_SECRET',
            'ALLOWED_HOSTS']
OS_EVARS_MISSING = [x for x in OS_EVARS if os.environ.get(x, None) is None]
if len(OS_EVARS_MISSING) > 0:
    raise Exception('Environment variables ({}) are missing!'.format(','.join(OS_EVARS_MISSING)))

SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = False
ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')

MIDDLEWARE += ['django.middleware.csrf.CsrfViewMiddleware']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'rpidrive',
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}

ARIA2_HOST = os.environ['ARIA2_HOST']
ARIA2_PORT = int(os.environ['ARIA2_PORT'])
ARIA2_SECRET = os.environ['ARIA2_SECRET']
