# ==================================================
# FILE: Mbayar/settings.py
# PATH: D:/Project Pyton/Mbayar/Mbayar/settings.py
# DESKRIPSI: Konfigurasi utama project Mbayar POS
# VERSION: 1.0.0
# UPDATE TERAKHIR: 03/03/2026
# ==================================================

import os
import dj_database_url
from pathlib import Path
from decouple import config

# ==================================================
# KONFIGURASI DASAR
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-default-key')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# ==================================================
# APLIKASI TERINSTAL
# ==================================================

INSTALLED_APPS = [
    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Third Party
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',

    # Local Apps
    'core',
]

# ==================================================
# MIDDLEWARE
# ==================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # <--- Tambah baris ini
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.EnsureProfileMiddleware',  # Memastikan setiap user memiliki profile
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.OutletMiddleware',         # Multi-outlet support
]

# ==================================================
# URL & TEMPLATE
# ==================================================

ROOT_URLCONF = 'Mbayar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'core/templates',
            BASE_DIR / 'core/templates/registration',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_info',
                'core.context_processors.outlet_info',
            ],
            'libraries': {
                'mbayar_tags': 'core.templatetags.mbayar_tags',
            }
        },
    },
]

WSGI_APPLICATION = 'Mbayar.wsgi.application'

# ==================================================
# DATABASE
# ==================================================

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600
    )
}

# ==================================================
# VALIDASI PASSWORD
# ==================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================================================
# INTERNASIONALISASI
# ==================================================

LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# ==================================================
# FILE STATIS & MEDIA
# ==================================================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Jika ada STATICFILES_DIRS, bisa dikomentari dulu untuk menghindari warning
# STATICFILES_DIRS = [BASE_DIR / 'core/static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==================================================
# KONFIGURASI UMUM
# ==================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login & Autentikasi
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'landing'

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 jam

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# ==================================================
# KONFIGURASI APLIKASI
# ==================================================

# Pajak
TAX_RATE = config('TAX_RATE', default=0.11, cast=float)

# Informasi Site
SITE_NAME = config('SITE_NAME', default='Mbayar POS')
SITE_VERSION = config('SITE_VERSION', default='1.0.0')

# GoFood
GOFOOD_FEE_PERCENT = 20

# ==================================================
# EMAIL (RESET PASSWORD)
# ==================================================

# Development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Production (uncomment untuk digunakan)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
# DEFAULT_FROM_EMAIL = 'Mbayar POS <noreply@mbayar.id>'

# Password Reset Timeout
PASSWORD_RESET_TIMEOUT = 3600  # 1 jam

# ==================================================
# AKHIR KONFIGURASI
# ==================================================