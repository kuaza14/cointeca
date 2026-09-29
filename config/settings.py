import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Carga el .env de la raiz si existe. Lo que ya venga en el entorno manda,
# asi docker compose sigue imponiendo sus propios valores.
#
# El import es opcional a proposito: si actualizas el codigo pero todavia no
# instalaste las dependencias nuevas, el proyecto arranca igual usando las
# variables de entorno y los valores por defecto.
try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv(BASE_DIR / '.env', override=False)

SECRET_KEY = (
    os.environ.get('DJANGO_SECRET_KEY')
    or 'django-insecure-f(s^*^neoun*u#m@qjah1#bigoa5hvfs6$ayn+_(_a#nivau7$'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('1', 'true', 'yes')

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
    if h.strip()
] or ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'core',  
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ModuloPermisosMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.alertas',
                'core.context_processors.permisos_usuario',
            ],
            'builtins': [
                'core.templatetags.filtros',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'cointeca_db'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'admin'),
        # Valores estandar para una instalacion local de PostgreSQL.
        # docker compose los sobrescribe (host 'db'); si en tu maquina el
        # 5432 esta ocupado, ponlo en un .env con POSTGRES_PORT.
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

database_url = os.environ.get('DATABASE_URL')
if database_url and dj_database_url:
    DATABASES['default'] = dj_database_url.config(
        default=database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )

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

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True

FORMAT_MODULE_PATH = [
    'config.formats',
]
DECIMAL_SEPARATOR = '.'
THOUSAND_SEPARATOR = ','
NUMBER_GROUPING = 3

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

csrf_origins = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:8001',
        'http://127.0.0.1:8001',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

import mimetypes
mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('application/pdf', '.pdf')

