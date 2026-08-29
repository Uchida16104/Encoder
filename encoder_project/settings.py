import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'encoder-development-secret-change-me')
DEBUG = os.environ.get('DJANGO_DEBUG', '0') == '1'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'converter',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'encoder_project.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
    ]},
}]

WSGI_APPLICATION = 'encoder_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'encoder.sqlite3',
    }
}

LANGUAGE_CODE = 'ja-jp'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
FILE_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

CSRF_TRUSTED_ORIGINS = [x for x in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if x]
