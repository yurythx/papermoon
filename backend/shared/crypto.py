"""
Criptografia simétrica para segredos guardados em repouso (ex: SSOConfiguration.client_secret).

A chave é derivada de SECRET_KEY via SHA-256 — não exige provisionar/rotacionar um
segredo separado. Efeito colateral: girar SECRET_KEY em produção invalida os valores
já criptografados (decrypt_secret volta "" nesse caso, nunca lança) — reconfigure o
segredo afetado (ex: reabra Configurações → SSO e salve o client_secret de novo).
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_secret(value: str) -> str:
    if not value:
        return ""
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return ""
