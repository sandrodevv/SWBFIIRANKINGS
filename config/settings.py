import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-change-in-production")

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "sass_processor",
    "apps.characters",
    "apps.rankings.apps.RankingsConfig",
    "apps.dashboard",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.rankings.middleware.VoterCookieMiddleware",
    "apps.rankings.middleware.WeeklyResetMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "frontend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres"):
    import re

    match = re.match(
        r"postgres(?:ql)?://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<name>.+)",
        DATABASE_URL,
    )
    if match:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": match.group("name"),
                "USER": match.group("user"),
                "PASSWORD": match.group("password"),
                "HOST": match.group("host"),
                "PORT": match.group("port"),
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "frontend" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "api.pagination.StandardPagination",
    "PAGE_SIZE": 22,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

VOTE_COOLDOWN_DAYS = 7
# Fixed weekly reset schedule (Python weekday: Monday=0 ... Sunday=6)
VOTE_RESET_WEEKDAY = int(os.getenv("VOTE_RESET_WEEKDAY", "6"))  # Sunday
VOTE_RESET_HOUR_UTC = int(os.getenv("VOTE_RESET_HOUR_UTC", "22"))
VOTE_RESET_MINUTE_UTC = int(os.getenv("VOTE_RESET_MINUTE_UTC", "0"))

# Discord webhooks (never hardcode; load from environment only)
# PFP weekly rankings embed
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# Player registration / ranked-player channel
DISCORD_RANKED_PLAYER_WEBHOOK_URL = os.getenv("DISCORD_RANKED_PLAYER_WEBHOOK_URL")
# EU duelist weekly winners (sent on weekly reset)
DISCORD_EU_DUELIST_WEBHOOK_URL = os.getenv("DISCORD_EU_DUELIST_WEBHOOK_URL")
# US duelist weekly winners (sent on weekly reset)
DISCORD_US_DUELIST_WEBHOOK_URL = os.getenv("DISCORD_US_DUELIST_WEBHOOK_URL")
# AU duelist weekly winners (sent on weekly reset)
DISCORD_AU_DUELIST_WEBHOOK_URL = os.getenv("DISCORD_AU_DUELIST_WEBHOOK_URL")
# Overall all-time duelist leaderboard (manual / snapshot)
DISCORD_OVERALL_ALLTIME_DUELIST_WEBHOOK_URL = os.getenv(
    "DISCORD_OVERALL_ALLTIME_DUELIST_WEBHOOK_URL"
)
DISCORD_WEBHOOK_TIMEOUT_SECONDS = float(os.getenv("DISCORD_WEBHOOK_TIMEOUT_SECONDS", "8"))
DISCORD_WEBHOOK_MAX_RETRIES = int(os.getenv("DISCORD_WEBHOOK_MAX_RETRIES", "3"))
DISCORD_WEBHOOK_BACKOFF_MULTIPLIER = float(
    os.getenv("DISCORD_WEBHOOK_BACKOFF_MULTIPLIER", "2.0")
)

# Automated PFP ending-soon notification
PFP_WEBHOOK_LEAD_MINUTES = int(os.getenv("PFP_WEBHOOK_LEAD_MINUTES", "10"))
PFP_WEBHOOK_TOP_N = int(os.getenv("PFP_WEBHOOK_TOP_N", "15"))
PFP_WEBHOOK_EMBED_COLOR = int(os.getenv("PFP_WEBHOOK_EMBED_COLOR", str(0xD4A843)))
DISCORD_REGISTRATION_EMBED_COLOR = int(
    os.getenv("DISCORD_REGISTRATION_EMBED_COLOR", str(0x57F287))
)
PFP_WEBHOOK_PENDING_CLAIM_TTL_SECONDS = int(
    os.getenv("PFP_WEBHOOK_PENDING_CLAIM_TTL_SECONDS", "300")
)
EU_DUELIST_WEBHOOK_TOP_N = int(os.getenv("EU_DUELIST_WEBHOOK_TOP_N", "16"))
EU_DUELIST_WEBHOOK_EMBED_COLOR = int(
    os.getenv("EU_DUELIST_WEBHOOK_EMBED_COLOR", str(0x3B82F6))
)
US_DUELIST_WEBHOOK_TOP_N = int(os.getenv("US_DUELIST_WEBHOOK_TOP_N", "16"))
US_DUELIST_WEBHOOK_EMBED_COLOR = int(
    os.getenv("US_DUELIST_WEBHOOK_EMBED_COLOR", str(0xEF4444))
)
AU_DUELIST_WEBHOOK_TOP_N = int(os.getenv("AU_DUELIST_WEBHOOK_TOP_N", "16"))
AU_DUELIST_WEBHOOK_EMBED_COLOR = int(
    os.getenv("AU_DUELIST_WEBHOOK_EMBED_COLOR", str(0x22C55E))
)
OVERALL_ALLTIME_DUELIST_WEBHOOK_TOP_N = int(
    os.getenv("OVERALL_ALLTIME_DUELIST_WEBHOOK_TOP_N", "16")
)
OVERALL_ALLTIME_DUELIST_WEBHOOK_EMBED_COLOR = int(
    os.getenv("OVERALL_ALLTIME_DUELIST_WEBHOOK_EMBED_COLOR", str(0xA855F7))
)

# Background scheduler (also triggered opportunistically from API middleware)
DISCORD_SCHEDULER_ENABLED = os.getenv("DISCORD_SCHEDULER_ENABLED", "True").lower() in (
    "true",
    "1",
    "yes",
)
DISCORD_SCHEDULER_INTERVAL_SECONDS = int(
    os.getenv("DISCORD_SCHEDULER_INTERVAL_SECONDS", "60")
)

LOGIN_URL = "/dashboard/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/dashboard/login/"

# Moderator dashboard login brute-force protection (per IP)
DASHBOARD_LOGIN_MAX_ATTEMPTS = 5
DASHBOARD_LOGIN_LOCKOUT_SECONDS = 900  # 15 minutes

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

SASS_PROCESSOR_ROOT = BASE_DIR / "frontend" / "static"
SASS_OUTPUT_STYLE = "compressed"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
]
