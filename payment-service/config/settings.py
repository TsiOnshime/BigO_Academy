from decouple import config 
from pathlib import Path 
BASE_DIR = Path(__file__).resolve().parent.parent 
SECRET_KEY = config('SECRET_KEY') 
DEBUG = config('DEBUG', default=False, cast=bool) 
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',') 
 
INSTALLED_APPS = [ 
    'django.contrib.admin', 
    'django.contrib.auth', 
    'django.contrib.contenttypes', 
    'django.contrib.sessions', 
    'django.contrib.messages', 
    'django.contrib.staticfiles', 
    'rest_framework', 
    'drf_spectacular',
    'core', 
] 
 
MIDDLEWARE = [ 
    'django.middleware.security.SecurityMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.common.CommonMiddleware', 
    'django.middleware.csrf.CsrfViewMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    'django.contrib.messages.middleware.MessageMiddleware', 
    'django.middleware.clickjacking.XFrameOptionsMiddleware', 
] 
 
ROOT_URLCONF = 'config.urls' 
 
TEMPLATES = [ 
    { 
        'BACKEND': 'django.template.backends.django.DjangoTemplates', 
        'DIRS': [], 
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
 
WSGI_APPLICATION = 'config.wsgi.application' 
 
DATABASES = { 
    'default': { 
        'ENGINE': 'django.db.backends.postgresql', 
        'NAME': config('DB_NAME'), 
        'USER': config('DB_USER'), 
        'PASSWORD': config('DB_PASSWORD'), 
        'HOST': config('DB_HOST', default='localhost'), 
        'PORT': config('DB_PORT', default='5432'), 
    } 
} 
 
LANGUAGE_CODE = 'en-us' 
TIME_ZONE = 'UTC' 
USE_I18N = True 
USE_TZ = True 
STATIC_URL = 'static/' 
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField' 
 
REST_FRAMEWORK = { 
    'DEFAULT_AUTHENTICATION_CLASSES': [], 
    'DEFAULT_PERMISSION_CLASSES': [], 
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'], 
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

} 
 
KAFKA_BOOTSTRAP_SERVERS = config('KAFKA_BOOTSTRAP_SERVERS', 
default='localhost:9092') 
 
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default='') 
JWT_ALGORITHM = config('JWT_ALGORITHM', default='HS256') 