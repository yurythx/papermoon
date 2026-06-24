import json

from .base import *

DEBUG = True

# ---------------------------------------------------------------------------
# JWT RS256 — gera par de chaves RSA em dev quando não definido no .env.
# A chave gerada é persistida em .jwt_dev_keys.json (gitignored) para que
# tokens permaneçam válidos entre reinicializações do servidor.
# ---------------------------------------------------------------------------
if not SIMPLE_JWT.get("SIGNING_KEY"):
    _keys_file = BASE_DIR / ".jwt_dev_keys.json"
    if _keys_file.exists():
        _dev_keys = json.loads(_keys_file.read_text())
        SIMPLE_JWT["SIGNING_KEY"] = _dev_keys["private"]
        SIMPLE_JWT["VERIFYING_KEY"] = _dev_keys["public"]
    else:
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa

            _private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )
            _private_pem = _private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode()
            _public_pem = (
                _private_key.public_key()
                .public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
                .decode()
            )
            _keys_file.write_text(json.dumps({"private": _private_pem, "public": _public_pem}))
            SIMPLE_JWT["SIGNING_KEY"] = _private_pem
            SIMPLE_JWT["VERIFYING_KEY"] = _public_pem
        except ImportError:
            import warnings

            warnings.warn(
                "cryptography not installed — JWT RS256 signing will fail. "
                "Run: pip install cryptography",
                stacklevel=2,
            )

try:
    import django_extensions  # noqa: F401

    INSTALLED_APPS += ["django_extensions"]
except ImportError:
    pass

# Logs mais verbosos em dev
LOGGING["root"]["level"] = "DEBUG"

# Rate limits generosos em dev — mesmos escopos do base para não quebrar testes de configuração
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update(
    {
        "anon": "1000/day",
        "user": "10000/day",
        "login": "100/minute",
        "token_refresh": "200/minute",
        "password_reset": "1000/day",  # sem limite real em dev — testes não devem ser bloqueados
        "register": "1000/day",
    }
)

# CORS aberto em dev
CORS_ALLOW_ALL_ORIGINS = True
