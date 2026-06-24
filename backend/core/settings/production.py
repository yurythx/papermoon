from django.core.exceptions import ImproperlyConfigured
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from .base import *

DEBUG = False

# ------------------------------------------------------------------
# JWT RS256 — chaves obrigatórias em produção.
# Gere um par com: make generate-jwt-keys
# ------------------------------------------------------------------
if not SIMPLE_JWT.get("SIGNING_KEY"):
    raise ImproperlyConfigured(
        "JWT_PRIVATE_KEY must be set in production. "
        "Generate a key pair with: make generate-jwt-keys"
    )
if not SIMPLE_JWT.get("VERIFYING_KEY"):
    raise ImproperlyConfigured(
        "JWT_PUBLIC_KEY must be set in production. Generate a key pair with: make generate-jwt-keys"
    )

# ------------------------------------------------------------------
# Security headers — Cloudflare Tunnel termina TLS; Django recebe HTTP puro.
#
# SECURE_SSL_REDIRECT = False: evita loop infinito (Django não sabe que a
# requisição original era HTTPS — quem faz o redirect é o Cloudflare via
# "Always Use HTTPS" na dashboard).
#
# SECURE_PROXY_SSL_HEADER: ensina Django a confiar no header X-Forwarded-Proto
# que o cloudflared injeta, para que cookies Secure sejam emitidos corretamente.
# ------------------------------------------------------------------
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

SECURE_HSTS_SECONDS = 31_536_000  # 1 ano — enviado no response; Cloudflare repassa
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Silence W008: SECURE_SSL_REDIRECT is intentionally False behind Cloudflare Tunnel.
SILENCED_SYSTEM_CHECKS = ["security.W008"]

# ------------------------------------------------------------------
# CORS — apenas o frontend registrado em CORS_ALLOWED_ORIGINS no .env
# ------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = False

# ------------------------------------------------------------------
# Database — reutilizar conexão por 60s reduz latência e carga no PG
# ------------------------------------------------------------------
DATABASES["default"]["CONN_MAX_AGE"] = 60

# ------------------------------------------------------------------
# Rate limiting mais conservador em produção
# ------------------------------------------------------------------
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(
    {
        "anon": "100/day",
        "user": "2000/day",
        "login": "5/minute",
        "token_refresh": "20/minute",
        "admin_write": "200/hour",
        "password_reset": "3/hour",  # Mais conservador em produção que o padrão de 5/h
    }
)

# ------------------------------------------------------------------
# Celery — limites de tempo por task evitam workers zumbis em produção
# ------------------------------------------------------------------
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 min: SoftTimeLimitExceeded (task pode limpar)
CELERY_TASK_TIME_LIMIT = 600  # 10 min: SIGKILL se ainda estiver rodando

# ------------------------------------------------------------------
# Sentry — só inicializa se DSN estiver configurado
# ------------------------------------------------------------------
if SENTRY_DSN:
    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.05,
            send_default_pii=False,
        )
    except Exception:
        import warnings

        warnings.warn(
            f"Sentry DSN inválido ({SENTRY_DSN!r}); error reporting desativado.", stacklevel=1
        )

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
LOGGING["root"]["level"] = "INFO"
