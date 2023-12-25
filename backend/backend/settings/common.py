import os
from pathlib import Path

from backend.settings.config import ConfigManager

ROOT_CONFIG = ConfigManager.load_config()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ROOT_CONFIG.web.secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ROOT_CONFIG.web.debug

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "rpidrive.apps.RpidriveConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.postgres",
]

CSRF_MIDDLEWARE = "django.middleware.csrf.CsrfViewMiddleware"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    CSRF_MIDDLEWARE,
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if DEBUG:
    MIDDLEWARE = [x for x in MIDDLEWARE if x != CSRF_MIDDLEWARE]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": ROOT_CONFIG.database.host,
        "PORT": ROOT_CONFIG.database.port,
        "NAME": ROOT_CONFIG.database.name,
        "USER": ROOT_CONFIG.database.user,
        "PASSWORD": ROOT_CONFIG.database.password,
        "CONN_MAX_AGE": 60,
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = ROOT_CONFIG.web.time_zone

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/drive/static/"
STATIC_ROOT = os.path.join(PROJECT_DIR, "static")

FILE_UPLOAD_TEMP_DIR = os.path.join(ROOT_CONFIG.web.temp_dir, "uploads")
os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{ROOT_CONFIG.redis.host}:{ROOT_CONFIG.redis.port}"
        f"/{ROOT_CONFIG.redis.db}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

LOG_DIR = ROOT_CONFIG.web.log_dir or os.path.join(os.path.dirname(BASE_DIR), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": ROOT_CONFIG.web.log_level,
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": ROOT_CONFIG.web.log_level,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "web.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10MB per file
            "backupCount": 10,
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": ROOT_CONFIG.web.log_level,
            "propagate": True,
        },
    },
}

LOGIN_URL = "/drive/login"

INIT_KEY_PATH = os.path.join(
    os.environ.get(
        ConfigManager._ENV_KEY,  # pylint: disable=protected-access
        os.path.dirname(BASE_DIR),
    ),
    "init.key",
)

BULK_BATCH_SIZE = 500

# Override default upload temp dir
FILE_UPLOAD_TEMP_DIR = os.path.join(ROOT_CONFIG.web.temp_dir, "uploads")

os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)
