"""
Django settings for proyecto project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

import os
import dj_database_url
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-5^v^wwx*vlo3gaixc4^pu6bbeb^9bkyx5pg0e7nu0cl-)6!w9y')

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['*']

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'app.Usuario'

INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',  # Nuestra aplicación
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
]

ROOT_URLCONF = 'proyecto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'app' / 'templates'],
        'APP_DIRS': False,   # False porque usamos loaders explícitos abajo
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyecto.wsgi.application'

# Base de datos (Supabase)
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
    }
else:
    # Fallback para desarrollo local si no hay URL configurada
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Archivos Estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Archivos Multimedia (imágenes de noticias, cursos, adjuntos de módulos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración de Supabase Storage (S3 API)
if os.environ.get('SUPABASE_S3_ACCESS_KEY'):
    AWS_S3_ENDPOINT_URL = os.environ.get('SUPABASE_S3_ENDPOINT')
    AWS_ACCESS_KEY_ID = os.environ.get('SUPABASE_S3_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = os.environ.get('SUPABASE_S3_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('SUPABASE_STORAGE_BUCKET_NAME')
    
    AWS_S3_REGION_NAME = 'us-east-1' # Normalmente us-east-1 o la de tu proyecto supabase
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    AWS_S3_FILE_OVERWRITE = False
    
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    # Usar almacenamiento local
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de Envío de Correos (Gmail SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# YouTube Embed Referrer Policy Fix
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Redirecciones de autenticación
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
