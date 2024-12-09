"""
Django settings for config project.
"""

from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
from rest_framework.permissions import AllowAny
import sys

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-9l3=^t!%#^v6l3@&6q=xz@)4_@0@8$0_$5l#)4@+_$0@8$0_$5')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '172.20.10.2', '*'] if DEBUG else os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'debug_toolbar',
    'django_filters',
    'mptt',
    'axes',
    'drf_spectacular',
    'rangefilter',
    
    # Local apps
    'accounts.apps.AccountsConfig',
    'products.apps.ProductsConfig',
    'cart.apps.CartConfig',
    'orders.apps.OrdersConfig',
    'mobile_payments.apps.MobilePaymentsConfig',
    'checkout.apps.CheckoutConfig',
    'analytics.apps.AnalyticsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'axes.middleware.AxesMiddleware',
    'config.middleware.SecurityHeadersMiddleware',
]

# Remove None values from MIDDLEWARE
MIDDLEWARE = [x for x in MIDDLEWARE if x is not None]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Site URL
SITE_URL = 'http://127.0.0.1:8002'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'auth': '50/hour',
    }
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Authentication settings
LOGIN_URL = '/admin/login/'
LOGOUT_URL = '/admin/logout/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# DRF Spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Urban Herb API',
    'DESCRIPTION': 'API for Urban Herb CBD E-commerce Platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter your bearer token in the format: Bearer <token>'
        }
    },
    'PREPROCESSING_HOOKS': [],
    'POSTPROCESSING_HOOKS': [],
    'DISABLE_ERRORS_AND_WARNINGS': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SCHEMA_COERCE_PATH_PK_SUFFIX': True,
    'SCHEMA_COERCE_METHOD_NAMES': {
        'retrieve': 'get',
        'destroy': 'delete'
    },
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication endpoints'},
        {'name': 'products', 'description': 'Product management endpoints'},
        {'name': 'cart', 'description': 'Shopping cart endpoints'},
        {'name': 'orders', 'description': 'Order management endpoints'},
        {'name': 'checkout', 'description': 'Checkout process endpoints'},
        {'name': 'payments', 'description': 'Payment processing endpoints'},
        {'name': 'analytics', 'description': 'Analytics and reporting endpoints'},
    ]
}

# Admin security settings
ADMIN_URL = 'admin/'  # Change in production
SECURE_ADMIN_URL = 'secure-admin/'  # Change in production
ADMIN_SITE_HEADER = 'Urban Herb Administration'
ADMIN_SITE_TITLE = 'Urban Herb Admin'
ADMIN_INDEX_TITLE = 'Administration'

# Session security settings
SESSION_COOKIE_AGE = 86400  # 24 hours in seconds
SESSION_COOKIE_SECURE = False  # Set to True in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # Changed from Strict to Lax for better compatibility
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CSRF settings
CSRF_COOKIE_SECURE = False  # Set to True in production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000', 
    'http://127.0.0.1:8000', 
    'http://localhost:8001', 
    'http://127.0.0.1:8001',
    'http://localhost:8002', 
    'http://127.0.0.1:8002',
    'http://172.20.10.2:8000',
]

# Security Middleware settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = False  # Set to True in production
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Django Axes settings
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_LOCKOUT_TEMPLATE = 'admin/login_lockout.html'
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address', 'user_agent']

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True  # Only for development
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8002',
    'http://127.0.0.1:8002',
]
CORS_ALLOWED_ORIGIN_REGEXES = []
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Debug toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG and 'test' not in sys.argv,
}

# Currency settings
from .currency import (
    CURRENCY, CURRENCY_SYMBOL, CURRENCY_DECIMAL_PLACES,
    CURRENCY_THOUSAND_SEPARATOR, CURRENCY_USE_GROUPING,
    MIN_AMOUNT, MAX_AMOUNT, format_currency
)

# Update number formatting settings
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = CURRENCY_THOUSAND_SEPARATOR
NUMBER_GROUPING = 3
DECIMAL_SEPARATOR = '.'

# Email settings
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Urban Herb <noreply@urbanherb.com>')

# Africa's Talking API settings
AT_API_KEY = os.getenv('AT_API_KEY')
AT_USERNAME = os.getenv('AT_USERNAME')
AT_SENDER_ID = os.getenv('AT_SENDER_ID', 'URBANHERB')

# Mobile Money API settings
MTN_API_KEY = os.getenv('MTN_API_KEY')
MTN_API_SECRET = os.getenv('MTN_API_SECRET')
MTN_WEBHOOK_SECRET = os.getenv('MTN_WEBHOOK_SECRET')

AIRTEL_API_KEY = os.getenv('AIRTEL_API_KEY')
AIRTEL_API_SECRET = os.getenv('AIRTEL_API_SECRET')
AIRTEL_WEBHOOK_SECRET = os.getenv('AIRTEL_WEBHOOK_SECRET')
