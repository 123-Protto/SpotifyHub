import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================
# BASE DIR
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# LOAD ENV (LOCAL ONLY – Render uses dashboard env vars)
# ============================================================
load_dotenv(BASE_DIR / ".env")

# ============================================================
# SECURITY
# ============================================================
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-local-dev-only"
)

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".onrender.com",
]

# Render proxy fix (IMPORTANT)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ============================================================
# INSTALLED APPS
# ============================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Project apps
    "core",
    "events",
    "store",
    "booking",

    # Third-party
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",

    "crispy_forms",
    "crispy_bootstrap5",
]

SITE_ID = 1
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ============================================================
# MIDDLEWARE (CORRECT ORDER)
# ============================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise MUST be right after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

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
# DATABASE (SQLite – OK for Render Free)
# ============================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ============================================================
# STATIC FILES (RENDER SAFE CONFIG)
# ============================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Only use STATICFILES_DIRS in LOCAL development
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / "static"]

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

# ============================================================
# MEDIA FILES
# ============================================================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ============================================================
# AUTH / ALLAUTH
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
# CSRF / SECURITY
# ============================================================
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://*.onrender.com",
]

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# ============================================================
# LANGUAGE / TIME
# ============================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ============================================================
# CASHFREE
# ============================================================
CASHFREE_CLIENT_ID = os.getenv("CASHFREE_CLIENT_ID")
CASHFREE_CLIENT_SECRET = os.getenv("CASHFREE_CLIENT_SECRET")

CASHFREE_BASE_URL = os.getenv(
    "CASHFREE_BASE_URL",
    "https://sandbox.cashfree.com/pg"
)

if not CASHFREE_CLIENT_ID or not CASHFREE_CLIENT_SECRET:
    print("⚠️ Cashfree keys missing")

# ============================================================
# EMAIL (DEV)
# ============================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ============================================================
# DEFAULT FIELD
# ============================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
