"""
Django settings for student_management_system project.
"""

import os
import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECRET_KEY = 'so*rai_2(lk7t(yh%de+_kp_c%*r_b9wkga%gyo5tl9_8_r!xx'

DEBUG = True

ALLOWED_HOSTS = ['*']

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'student_management_app',
    'django.contrib.sites',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'student_management_app.LoginCheckMiddleWare.LoginCheckMiddleWare',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

# Single, correct database configuration for Render PostgreSQL
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get(
            'DATABASE_URL',
            'postgresql://student_management_db_django_render_user:fxUChmVWj2YXEclQBeRzwAW5W8UEpUo8@dpg-d2fknjbe5dus73asppi0-a.oregon-postgres.render.com/student_management_db_django_render',
        )
    )
}

ROOT_URLCONF = 'student_management_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['student_management_app/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'builtins': [
                'django.templatetags.static',
                'django.templatetags.l10n',
                'django.templatetags.i18n',
                'django.templatetags.tz',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'student_management_system.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.NumericPasswordValidator'
        ),
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTH_USER_MODEL = 'student_management_app.CustomUser'
AUTHENTICATION_BACKENDS = [
    'student_management_app.EmailBackEnd.EmailBackEnd'
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = '56.negilalit@gmail.com'
EMAIL_HOST_PASSWORD = 'qnjg gmzz ijjq rjhs'
DEFAULT_FROM_EMAIL = 'Student Management <56.negilalit@gmail.com>'