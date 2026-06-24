from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))

_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(_env_file)

def _env_first(*names: str, default: str = "") -> str:
    for name in names:
        value = env(name, default="")
        if value:
            return value
    return default


SECRET_KEY = _env_first("PAPERMOON_SECRET_KEY", "SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

AUTH_USER_MODEL = "accounts.CustomUser"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_celery_beat",
    "django_filters",
    # internal
    "shared",
    "apps.accounts",
    "apps.customers",
    "apps.billing",
    "apps.licensing",
    "apps.support",
    "apps.audit",
    "apps.notifications",
    "apps.products",
    "apps.subscriptions",
    "apps.provisioning",
    "apps.cms",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Security headers — safe for all environments; hardened further in production.py
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

ROOT_URLCONF = "core.urls"

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
    },
]

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "CONN_MAX_AGE": 60,  # Reutiliza conexão por até 60s — reduz overhead de handshake
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
        "shared.permissions.IsActiveCustomer",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "shared.renderers.UnifiedResponseRenderer",
    ],
    "EXCEPTION_HANDLER": "shared.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "200/day",
        "user": "1000/day",
        "login": "5/minute",
        "token_refresh": "20/minute",
        "admin_write": "100/hour",
        "password_reset": "5/hour",  # Previne bomba de e-mail e força-bruta de tokens
        "contact": "5/hour",
        "register": "5/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
}

# --- Simple JWT (RS256) ---
# Keys are loaded from env; local.py auto-generates a dev pair when absent.
# Production must set JWT_PRIVATE_KEY and JWT_PUBLIC_KEY explicitly.
# PEM strings in .env use literal \n — replaced here to actual newlines.
SIMPLE_JWT = {
    "ALGORITHM": "RS256",
    "SIGNING_KEY": env("JWT_PRIVATE_KEY", default="").replace("\\n", "\n"),
    "VERIFYING_KEY": env("JWT_PUBLIC_KEY", default="").replace("\\n", "\n"),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

# --- Redis / Celery ---
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# --- CORS ---
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

# --- Asaas ---
ASAAS_API_KEY = env("ASAAS_API_KEY", default="")
ASAAS_WEBHOOK_TOKEN = env("ASAAS_WEBHOOK_TOKEN", default="")

# --- Chatwoot ---
CHATWOOT_API_URL = env("CHATWOOT_API_URL", default="")
CHATWOOT_API_KEY = env("CHATWOOT_API_KEY", default="")

# --- Cache (Redis) ---
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# --- OpenAPI / Spectacular ---
SPECTACULAR_SETTINGS = {
    "TITLE": "PaperMoon API",
    "DESCRIPTION": "Backend SaaS multi-tenant do ecossistema PaperMoon para gerenciamento de clientes, faturamento, licenciamento e operacoes.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "CustomerStatusEnum": "apps.customers.models.Customer.Status",
        "SubscriptionStatusEnum": "apps.subscriptions.models.Subscription.Status",
        "InvoiceStatusEnum": "apps.billing.models.Invoice.Status",
        "LicenseStatusEnum": "apps.subscriptions.models.License.Status",
        "ServiceAccessStatusEnum": "apps.subscriptions.models.ServiceAccess.Status",
        "InvitationStatusEnum": "apps.customers.models.Invitation.Status",
        "NotificationStatusEnum": "apps.notifications.models.Notification.Status",
    },
}

# --- Sentry ---
SENTRY_DSN = env("SENTRY_DSN", default="")

# --- E-mail ---
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
# Accept PAPERMOON_* aliases while keeping current env names valid during migration.
DEFAULT_FROM_EMAIL = _env_first(
    "PAPERMOON_DEFAULT_FROM_EMAIL",
    "DEFAULT_FROM_EMAIL",
    default="noreply@papermoon.local",
)

# --- Frontend ---
FRONTEND_URL = _env_first(
    "PAPERMOON_FRONTEND_URL",
    "FRONTEND_URL",
    default="http://localhost:3000",
).rstrip("/")
MEDIA_PUBLIC_BASE_URL = _env_first(
    "PAPERMOON_MEDIA_PUBLIC_BASE_URL",
    "MEDIA_PUBLIC_BASE_URL",
    default="",
).rstrip("/")
ADMIN_NOTIFICATION_EMAIL = _env_first(
    "PAPERMOON_ADMIN_NOTIFICATION_EMAIL",
    "ADMIN_NOTIFICATION_EMAIL",
    default="",
)

# --- Telegram ops alerts (optional) ---
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_ALERT_CHAT_ID = env("TELEGRAM_ALERT_CHAT_ID", default="")

# --- CMS / ISR revalidation ---
NEXTJS_INTERNAL_URL = _env_first(
    "PAPERMOON_NEXTJS_INTERNAL_URL",
    "NEXTJS_INTERNAL_URL",
    default="http://nextjs:3000",
)
REVALIDATE_SECRET = _env_first(
    "PAPERMOON_REVALIDATE_SECRET",
    "REVALIDATE_SECRET",
    default="",
)

# --- n8n ---
N8N_API_URL = env("N8N_API_URL", default="")
N8N_API_KEY = env("N8N_API_KEY", default="")

# --- Meta WhatsApp Business API ---
META_WHATSAPP_TOKEN = env("META_WHATSAPP_TOKEN", default="")
META_WABA_ID = env("META_WABA_ID", default="")

# --- GLPI ---
GLPI_API_URL = env("GLPI_API_URL", default="")
GLPI_APP_TOKEN = env("GLPI_APP_TOKEN", default="")
GLPI_USER_TOKEN = env("GLPI_USER_TOKEN", default="")

# --- Zabbix ---
ZABBIX_API_URL = env("ZABBIX_API_URL", default="")
ZABBIX_API_TOKEN = env("ZABBIX_API_TOKEN", default="")

# --- TrueNAS ---
TRUENAS_API_URL = env("TRUENAS_API_URL", default="")
TRUENAS_API_KEY = env("TRUENAS_API_KEY", default="")
TRUENAS_POOL = env("TRUENAS_POOL", default="data")

# --- RustDesk Server Pro ---
RUSTDESK_API_URL = env("RUSTDESK_API_URL", default="")
RUSTDESK_API_KEY = env("RUSTDESK_API_KEY", default="")

# --- Windows Server (Windows Admin Center) ---
WINDOWS_SERVER_WAC_URL = env("WINDOWS_SERVER_WAC_URL", default="")
WINDOWS_SERVER_WAC_KEY = env("WINDOWS_SERVER_WAC_KEY", default="")

# --- Samba (Linux file server) ---
SAMBA_API_URL = env("SAMBA_API_URL", default="")
SAMBA_API_KEY = env("SAMBA_API_KEY", default="")

# --- Logging base (JSON estruturado) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "shared.logging.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {"level": "INFO", "propagate": True},
        "celery": {"level": "INFO", "propagate": True},
        "apps": {"level": "INFO", "propagate": True},
        "shared": {"level": "INFO", "propagate": True},
    },
}
