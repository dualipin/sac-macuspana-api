from datetime import timedelta
from email.headerregistry import Address

import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DATABASE_ENGINE=(str, "sqlite3"),
)
environ.Env.read_env(BASE_DIR / '.env')

# Secrets keys
SECRET_KEY = env('DJANGO_SECRET_KEY')
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DJANGO_DEBUG')

# Externals API URLs
CURP_API_URL = env("CURP_API_URL")
WEB_URL = env("WEB_URL")

# Allowed hosts
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"] if DEBUG else [])

# CORS settings
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST", "smtp.example.com")
EMAIL_PORT = env.int("EMAIL_PORT", 587)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", cast=bool, default=True)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "tu_email@example.com")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "tu_contraseña")
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = Address(display_name="SAC Macuspana", addr_spec=EMAIL_HOST_USER)
# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    # 'django.contrib.staticfiles',
    'django_filters',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'encrypted_model_fields',
    'corsheaders',
    'simple_history',

    # Local apps
    'apoyos',
    'ciudadanos',
    'dependencias',
    'localidades',
    'servicios',
    'tramites',
    'usuarios',
    'notificaciones'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware'
]

ROOT_URLCONF = 'config.urls'

AUTH_USER_MODEL = 'usuarios.Usuario'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases


DATABASE_ENGINE = env("DATABASE_ENGINE")

if DATABASE_ENGINE == "sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": env("DATABASE_HOST", default="localhost"),
            "USER": env("DATABASE_USER", default="user"),
            "PASSWORD": env("DATABASE_PASSWORD", default="password"),
            "NAME": env("DATABASE_NAME", default="db_name"),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "es-MX"

TIME_ZONE = "America/Mexico_City"

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Media files (User uploads)
# Guardamos los archivos subidos en la carpeta "media" en la raíz del proyecto
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# JWT Config
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,  # Invalida el refresh token anterior al usarlo
}

# REST Framework settings
REST_FRAMEWORK = {
    # "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # "rest_framework.authentication.TokenAuthentication",
        # "rest_framework.authentication.BasicAuthentication",
    ],
    # "DEFAULT_PERMISSION_CLASSES": [
    #     "rest_framework.permissions.IsAuthenticated"
    # ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,  # Aumentado de 9 para mejor UX con scroll infinito
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
