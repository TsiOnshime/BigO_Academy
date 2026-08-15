from decouple import config 
from pathlib import Path 
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent 
SECRET_KEY = config('SECRET_KEY') 
DEBUG = config('DEBUG', default=False, cast=bool) 
ALLOWED_HOSTS = [
    host.strip()
    for host in str(config('ALLOWED_HOSTS', default='localhost')).split(',')
    if host.strip()
]
 
INSTALLED_APPS = [ 
    'corsheaders',
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
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware', 
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.common.CommonMiddleware', 
    'django.middleware.csrf.CsrfViewMiddleware', 
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    'django.contrib.messages.middleware.MessageMiddleware', 
    'django.middleware.clickjacking.XFrameOptionsMiddleware', 
] 


CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "https://big-o-academy-frontend.vercel.app",
]
CORS_ALLOW_CREDENTIALS = True
 
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
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=0,
        ssl_require=True
    )
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

JWT_SECRET_KEY = config(
    'JWT_SECRET_KEY',
    default='django-insecure-^s0)!65!%2sgjnpdp%_v__!)353^s^sscl=mi(!tjfge_scf!9',
)
JWT_ALGORITHM = config('JWT_ALGORITHM', default='HS256') 


STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'