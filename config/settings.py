from pathlib import Path
import os
import logging
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from config.unfold import *

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
SITE_DOMAIN = os.environ.get('SITE_DOMAIN')
SITE_URL = f'https://{SITE_DOMAIN}'
SITE_IP = os.environ.get('SITE_IP')
ALLOWED_HOSTS = [SITE_DOMAIN, SITE_IP, '127.0.0.1', '0.0.0.0']
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin-allow-popups'

if not DEBUG:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )
else:
    logging.basicConfig(
        filename='.log',
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        level=logging.INFO
    )

logger = logging.getLogger(__name__)

LESS_LOG_PACKAGES = ['requests', 'urllib3', 'openai', 'httpx', 'httpcore']
for package in LESS_LOG_PACKAGES:
    logging.getLogger(package).setLevel(logging.WARNING)

CSRF_TRUSTED_ORIGINS = [
    f'https://{SITE_DOMAIN}',
    f'http://{SITE_DOMAIN}',
    f'http://{SITE_IP}',
    f'https://{SITE_IP}',
    'http://127.0.0.1:8000',
]
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    "unfold.contrib.location_field",
    "unfold.contrib.constance",
    "django.contrib.admin",

    "django_ckeditor_5",
    "crispy_forms",
    "django_jsonform",
    'django_cleanup.apps.CleanupConfig',
    'import_export',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # apps
    'apps.core',
    'apps.accounts',
    'apps.business_profile',
    'apps.webhooks',
    'apps.credit',
]
CRISPY_TEMPLATE_PACK = "unfold_crispy"
CRISPY_ALLOWED_TEMPLATE_PACKS = ["unfold_crispy"]
CKEDITOR_5_CONFIGS = {
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3',
            '|', 'bulletedList', 'numberedList',
            '|', 'blockQuote',
        ],
        
        'toolbar': {
            'items': [
                'heading', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough',
                'code', 'highlight', '|',
                'bulletedList', 'numberedList', '|', 'outdent', 'indent',
                
                '-',
                
                'blockQuote', 'insertTable', '|',
                'imageUpload', 'mediaEmbed', 'sourceEditing', '|', 'undo', 'redo',
            ],
            'shouldNotGroupWhenFull': True, 
        },
        
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignCenter', 'imageStyle:alignRight'],
            'styles': ['alignLeft', 'alignCenter', 'alignRight']
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells'],
        },
    }
}
SITE_ID = 1
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # allauth
    "allauth.account.middleware.AccountMiddleware",
]
ROOT_URLCONF = 'config.urls'
AUTH_USER_MODEL = 'accounts.User'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.google_tag_manager',
            ],
            'libraries': {
                'string_utils': 'apps.core.templatetags.string_utils',
                'time_utils': 'apps.core.templatetags.time_utils',
            }
        },
    },
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

WSGI_APPLICATION = 'config.wsgi.application'

import urllib.parse as urlparse

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        urlparse.uses_netloc.append('postgres')
        urlparse.uses_netloc.append('postgresql')
        url = urlparse.urlparse(db_url)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': url.path[1:],
                'USER': url.username,
                'PASSWORD': url.password,
                'HOST': url.hostname,
                'PORT': url.port or 5432,
                'CONN_MAX_AGE': 60,
                'OPTIONS': {
                    'sslmode': 'require',
                },
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME'),
                'USER': os.environ.get('DB_USER'),
                'PASSWORD': os.environ.get('DB_PASSWORD'),
                'HOST': os.environ.get('DB_HOST'),
                'PORT': os.environ.get('DB_PORT', 5432),
                'CONN_MAX_AGE': 60,
                'OPTIONS': {
                    'sslmode': os.environ.get('DB_SSLMODE', 'require'),
                },
            }
        }


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


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_MANIFEST_STRICT = False


# facebook/whatsapp oauth settings
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET')
FACEBOOK_VERIFY_TOKEN = os.environ.get('FACEBOOK_VERIFY_TOKEN')
FACEBOOK_REDIRECT_URI = f'{SITE_URL}/business-profile/facebook/callback/'
WHATSAPP_REDIRECT_URI = f'{SITE_URL}/business-profile/whatsapp/callback/'
FACEBOOK_GRAPH_API_VERSION = 'v25.0'
FACEBOOK_GRAPH_API_URL = f'https://graph.facebook.com/{FACEBOOK_GRAPH_API_VERSION}'
WHATSAPP_EMBEDDED_SIGNUP_CONFIG_ID = os.environ.get('WHATSAPP_EMBEDDED_SIGNUP_CONFIG_ID')

# encryption settings
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY').encode()
FERNET = Fernet(ENCRYPTION_KEY)

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
MAIN_EMAIL = os.environ.get('MAIN_EMAIL')
if os.environ.get('MAIN_EMAIL_HOST_PASSWORD'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = MAIN_EMAIL 
EMAIL_HOST_PASSWORD = os.environ.get('MAIN_EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = f'Cholbe AI <{MAIN_EMAIL}>'

# CUSTOM SETTINGS
with open(BASE_DIR / 'config/default_system_prompt.txt') as f:
    DEFAULT_SYSTEM_PROMPT = f.read()
with open(BASE_DIR / 'config/default_business_info.txt') as f:
    DEFAULT_BUSINESS_INFO = f.read()
DEFAULT_AI_MODEL = 'google/gemma-4-31b-it:free'
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
GOOGLE_TAG_MANAGER_ID = os.environ.get('GOOGLE_TAG_MANAGER_ID', '')

PAYMENT_ADAPTER = os.environ.get('PAYMENT_ADAPTER', 'manual')
MANUAL_PAYMENT_NUMBER = os.environ.get('MANUAL_PAYMENT_NUMBER', '01XXXXXXXXX')

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

## allauth settings
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_NOTIFICATIONS = True
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
LOGIN_REDIRECT_URL = "/d/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
if DEBUG:
    ACCOUNT_RATE_LIMITS = False
ACCOUNT_ADAPTER = 'apps.accounts.adapter.CustomAccountAdapter'
ACCOUNT_FORMS = {
    'login': 'apps.accounts.forms.CustomLoginForm',
    'signup': 'apps.accounts.forms.CustomSignupForm',
    'add_email': 'apps.accounts.forms.CustomAddEmailForm',
    'change_password': 'apps.accounts.forms.CustomChangePasswordForm',
    'set_password': 'apps.accounts.forms.CustomSetPasswordForm',
    'reset_password': 'apps.accounts.forms.CustomResetPasswordForm',
    'reset_password_from_key': 'apps.accounts.forms.CustomResetPasswordKeyForm',
    'confirm_email_verification_code': 'apps.accounts.forms.CustomConfirmEmailVerificationCodeForm',
}

SOCIALACCOUNT_ADAPTER = 'apps.accounts.adapter.CustomSocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_STORE_TOKENS = True
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'FETCH_USERINFO': True,
        'VERIFIED_EMAIL': True,
    },
}
