import os.path
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-!d)e1)+(6jd9i4=)j--cdh*@wf&dyhrq99qf(loc12uxn*)u@9'

DEBUG = True

ALLOWED_HOSTS = [
  '62.60.237.139',
  'localhost',
  '127.0.0.1',
  "morphism.pro",
  "www.morphism.pro",
  "nordemaison.shop",
  "www.nordemaison.shop",
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',
    'tinymce',
    'colorfield',
    'corsheaders',
    'image_uploader_widget',
    'adminsortable2',
    'catalog',
    'users',
    'favorites',
    'cart',
    'orders',
    'shop_config',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'norde_maison.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'norde_maison.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'norde_maison',
        'USER': 'postgres',
        'PASSWORD': 'admin',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

TINYMCE_DEFAULT_CONFIG = {
    "height": 420,
    "width": "100%",
    "menubar": False,
    "plugins": "lists",
    "toolbar": "undo redo | blocks | bold italic | bullist numlist",
    "valid_elements": "p,h3,strong,em,ul,ol,li",
    "block_formats": "Paragraph=p; Заголовок=h3",
    "paste_as_text": True,
    "paste_block_drop": True,
    "invalid_elements": "a",
    "skin": "oxide-dark",
    "content_css": "dark",
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
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
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'https://127.0.0.1:8000',
    'https://localhost:8000',
    "https://norde-maison-frontend.vercel.app"
]

CSRF_TRUSTED_ORIGINS = [
    "https://morphism.pro",
    "https://www.morphism.pro",
    "https://nordemaison.shop",
    "https://www.nordemaison.shop",
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

#SITE_URL = "https://127.0.0.1:8000"
SITE_URL = "https://nordemaison.shop"

#SITE_URL_CLIENT = "http://localhost:5173"
SITE_URL_CLIENT = "https://norde-maison-frontend.vercel.app"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.yandex.com"
EMAIL_PORT = 465
EMAIL_USE_SSL = True

EMAIL_HOST_USER = "alexygarnov@yandex.ru"
EMAIL_HOST_PASSWORD = "tttglfubsolxieup"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

YOOKASSA_SHOP_ID = "1305307"
YOOKASSA_SECRET_KEY = "test_Gvf9reEgzw9GF_24Sn3tutuNxSX5q4ODJc9VfbWar14"
YOOKASSA_RETURN_URL = f"{SITE_URL_CLIENT}/profile/"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True