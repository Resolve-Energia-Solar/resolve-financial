from datetime import timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
from .jazzmin import JAZZMIN_SETTINGS, JAZZMIN_UI_TWEAKS

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')


DEBUG = (os.environ.get('DEBUG') == 'True')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(',') if os.environ.get('ALLOWED_HOSTS') else []
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS').split(',') if os.environ.get('CSRF_TRUSTED_ORIGINS') else []

# if not DEBUG:
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_SSL_REDIRECT = True
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#     SECURE_HSTS_SECONDS = 3156000
#     SECURE_HSTS_PRELOAD = True
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     USE_X_FORWARDED_HOST = True


INSTALLED_APPS = [
    'jazzmin',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    "debug_toolbar",
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',
    'core.apps.CoreConfig',
    'resolve_crm.apps.ResolveCRMConfig',
    'contracts.apps.ContractsConfig',
    'logistics.apps.LogisticsConfig',
    'field_services.apps.FieldServicesConfig',
    'engineering.apps.EngineeringConfig',
    'financial.apps.FinancialConfig',
    'mobile_app.apps.MobileAppConfig',
    'notifications',
    'simple_history',
    'api.apps.ApiConfig',
    'rest_framework',
    'drf_yasg',
    'django_filters',
    'corsheaders',
    'channels',
]

ASGI_APPLICATION = 'resolve_erp.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('redis', 6379)], 
        },
    },
}

DJANGO_NOTIFICATIONS_CONFIG = {'SOFT_DELETE': True}

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

# REST_FLEX_FIELDS = {
#     'SERIALIZER_EXTENSIONS': [
#         'accounts.serializers',
#         'core.serializers',
#         'resolve_crm.serializers',
#         'contracts.serializers',
#         'logistics.serializers',
#         'field_services.serializers',
#         'engineering.serializers',
#         'financial.serializers',
#         'mobile_app.serializers',
#         'api.serializers',
#     ],
# }

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    # Removemos o painel de histórico que está quebrando
    # 'debug_toolbar.panels.history.HistoryPanel',
]


CELERY_BROKER_URL = "amqp://guest:guest@rabbitmq:5672//"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_RESULT_BACKEND = "rpc://"

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

# CORS

CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS') == 'True'

CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS').split(',') if os.environ.get('CORS_ALLOWED_ORIGINS') else []

CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS') == 'True'

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]

CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
]


# URLs

ROOT_URLCONF = 'resolve_erp.urls'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'


# Templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates/'],
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

WSGI_APPLICATION = 'resolve_erp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get("DB1_NAME"),
        'USER': os.environ.get("DB1_USER"),
        'PASSWORD': os.environ.get("DB1_PASSWORD"),
        'HOST': os.environ.get("DB1_HOST"),
        'PORT': os.environ.get("DB1_PORT"),
        'CONN_MAX_AGE': 300
    }
}

# choose the database to use
DATABASES['default'] = DATABASES[os.environ.get('DB_USED')]


# Google Cloud Storage
GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME')
GS_LOCATION = os.getenv('GS_LOCATION')
GOOGLE_APPLICATION_CREDENTIALS=os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {}
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

SIMPLE_HISTORY_HISTORY_ID_USE_UUID = False
# SIMPLE_HISTORY_ENABLED = True


# User model
AUTH_USER_MODEL = "accounts.User"

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.CustomPagination',
    'PAGE_SIZE': 10,
    # 'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}


SIMPLE_JWT = {
    # Definindo a expiração do token de acesso para uma hora
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    # Tempo de vida do token de atualização
    "REFRESH_TOKEN_LIFETIME": timedelta(days=15),
}


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Belem'

USE_I18N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Configuração de envio de e-mail
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')


# Admins
ADMINS = [
    (os.getenv('ADMIN_NAME'), os.getenv('ADMIN_EMAIL')),
]

# Configuração do Logging

if DEBUG == False:
    
    import logging
    import logging.handlers

    
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "-"*60 + "\n{levelname} {asctime} {module} {process:d} {thread:d} {message}",
                "style": "{",
            },
        },
        "filters": {
            "debug_filter": {
                "()": "django.utils.log.CallbackFilter",
                "callback": lambda record: record.levelno == logging.DEBUG,
            },
            "info_filter": {
                "()": "django.utils.log.CallbackFilter",
                "callback": lambda record: record.levelno == logging.INFO,
            },
            "warning_filter": {
                "()": "django.utils.log.CallbackFilter",
                "callback": lambda record: record.levelno == logging.WARNING,
            },
            "error_filter": {
                "()": "django.utils.log.CallbackFilter",
                "callback": lambda record: record.levelno == logging.ERROR,
            },
            "critical_filter": {
                "()": "django.utils.log.CallbackFilter",
                "callback": lambda record: record.levelno == logging.CRITICAL,
            },
        },
        "handlers": {
            "mail_admins": {
                "level": "ERROR",
                "class": "django.utils.log.AdminEmailHandler",
                "include_html": True,
                "formatter": "verbose",
            },
            "debug_file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/debug.log",
                "formatter": "verbose",
                "maxBytes": 50 * 1024 * 1024,
                "backupCount": 10,
                "filters": ["debug_filter"],
            },
            "info_file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/info.log",
                "formatter": "verbose",
                "maxBytes": 50 * 1024 * 1024,
                "backupCount": 10,
                "filters": ["info_filter"],
            },
            "warning_file": {
                "level": "WARNING",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/warning.log",
                "formatter": "verbose",
                "maxBytes": 50 * 1024 * 1024,
                "backupCount": 10,
                "filters": ["warning_filter"],
            },
            "error_file": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/error.log",
                "formatter": "verbose",
                "maxBytes": 50 * 1024 * 1024,
                "backupCount": 10,
                "filters": ["error_filter"],
            },
            "critical_file": {
                "level": "CRITICAL",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/critical.log",
                "formatter": "verbose",
                "maxBytes": 50 * 1024 * 1024,
                "backupCount": 10,
                "filters": ["critical_filter"],
            },
        },
        "loggers": {
            "django": {
                "handlers": ["mail_admins"],
                "level": "ERROR",
                "propagate": True,
            },
            "": {
                "handlers": ["debug_file", "info_file", "warning_file", "error_file", "critical_file"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }

    LOGGING["handlers"]["debug_file"]["filters"] = ["debug_filter"]
    LOGGING["handlers"]["info_file"]["filters"] = ["info_filter"]
    LOGGING["handlers"]["warning_file"]["filters"] = ["warning_filter"]
    LOGGING["handlers"]["error_file"]["filters"] = ["error_filter"]
    LOGGING["handlers"]["critical_file"]["filters"] = ["critical_filter"]


JAZZMIN_SETTINGS = JAZZMIN_SETTINGS
# JAZZMIN_SETTINGS["show_ui_builder"] = True