from __future__ import annotations

import ipaddress
from typing import Mapping
from urllib.parse import urlencode, urlsplit, urlunsplit

from django.conf import settings


def build_frontend_url(path: str, params: Mapping[str, object] | None = None) -> str:
    clean_path = "/" + path.lstrip("/")
    query = urlencode(
        [(key, value) for key, value in (params or {}).items() if value is not None],
        doseq=True,
    )
    return f"{settings.FRONTEND_URL}{clean_path}" + (f"?{query}" if query else "")


def build_public_media_url(file_url: str | None, request=None) -> str | None:
    if not file_url:
        return None
    if file_url.startswith(("http://", "https://")):
        return file_url
    public_base = getattr(settings, "MEDIA_PUBLIC_BASE_URL", "")
    if public_base:
        return f"{public_base.rstrip('/')}/{file_url.lstrip('/')}"
    if request is not None:
        return request.build_absolute_uri(file_url)
    return file_url


def sanitize_public_url(
    url: str | None,
    *,
    allowed_domains: tuple[str, ...] | None = None,
    allow_localhost: bool = False,
) -> str | None:
    if not url:
        return None

    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None

    if hostname == "localhost":
        return urlunsplit(parsed) if allow_localhost else None

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        if allowed_domains and not _host_matches_allowed_domains(hostname, allowed_domains):
            return None
        if "." not in hostname:
            return None
        return urlunsplit(parsed)

    if ip.is_loopback:
        return urlunsplit(parsed) if allow_localhost else None
    if ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
        return None
    return urlunsplit(parsed)


def sanitize_payment_url(url: str | None) -> str | None:
    return sanitize_public_url(
        url,
        allowed_domains=("asaas.com", "asaas.com.br"),
        allow_localhost=False,
    )


def _host_matches_allowed_domains(hostname: str, allowed_domains: tuple[str, ...]) -> bool:
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains)
