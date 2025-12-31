import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# BASE DIR
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# LOAD ENV (LOCAL ONLY)
# ============================================================
load_dotenv(BASE_DIR / ".env")

# ============================================================
# SECURITY
# ============================================================
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-fallback-only-for-local-dev"
)

DEBUG = os.getenv("DEBUG", "False").lower() == "true"


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".onrender.com",
    "*",  # Safe for Render
]

# Render / proxy SSL fix
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ============================================================
# INSTALLED APPS
# ============================================================
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # Project apps
    "core",
    "events",
    "booking",
    "store",

    # Third-party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "crispy_forms",
    "crispy_bootstrap5",
    "cloudinary",
    "cloudinary_storage",
]

SITE_ID = 1
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ============================================================
# MIDDLEWARE (ORDER IS CRITICAL)
# ============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise must be directly after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # Allauth
    "allauth.account.middleware.AccountMiddleware",
]

# ============================================================
# URL / WSGI
# ============================================================
ROOT_URLCONF = "rural_sports.urls"
WSGI_APPLICATION = "rural_sports.wsgi.application"

# ============================================================
# TEMPLATES
# ============================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# ============================================================
# DATABASE (SQLite – Render Free Tier Friendly)
# ============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ============================================================
# STATIC FILES (RENDER SAFE)
# ============================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / "static"]


# ============================================================
# CLOUDINARY (MEDIA FILES)
# ============================================================
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
}

# ============================================================
# STORAGE BACKENDS (DJANGO 5.2+)
# ============================================================
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ============================================================
# AUTHENTICATION / ALLAUTH
# ============================================================
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
LOGIN_URL = "/accounts/login/"

ACCOUNT_LOGIN_BY_EMAIL = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "email2*",
    "username*",
    "password1*",
    "password2*",
]

ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/m",
}

# ============================================================
# CSRF & COOKIE SECURITY
# ============================================================
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://spotifyhub.onrender.com",
]

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# ============================================================
# LANGUAGE & TIMEZONE
# ============================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ============================================================
# CASHFREE PAYMENT GATEWAY
# ============================================================
CASHFREE_CLIENT_ID = os.getenv("CASHFREE_CLIENT_ID")
CASHFREE_CLIENT_SECRET = os.getenv("CASHFREE_CLIENT_SECRET")

CASHFREE_BASE_URL = os.getenv(
    "CASHFREE_BASE_URL",
    "https://sandbox.cashfree.com/pg"
)
CASHFREE_WEBHOOK_URL = os.getenv("CASHFREE_WEBHOOK_URL")
CASHFREE_BOOKING_WEBHOOK_URL = os.getenv("CASHFREE_BOOKING_WEBHOOK_URL")



# ============================================================
# EMAIL (DEV DEFAULT)
# ============================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
