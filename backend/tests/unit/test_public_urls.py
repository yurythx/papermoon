from unittest.mock import Mock

import pytest

from shared.public_urls import (
    build_frontend_url,
    build_public_media_url,
    sanitize_payment_url,
    sanitize_public_url,
)


def test_build_frontend_url_normalizes_path_and_query(settings):
    settings.FRONTEND_URL = "https://app.papermoon.com.br"

    url = build_frontend_url("reset-password", params={"uid": "abc", "token": "xyz", "skip": None})

    assert url == "https://app.papermoon.com.br/reset-password?uid=abc&token=xyz"


def test_build_frontend_url_supports_sequence_params(settings):
    settings.FRONTEND_URL = "https://app.papermoon.com.br"

    url = build_frontend_url("/filters", params={"tag": ["billing", "overdue"]})

    assert url == "https://app.papermoon.com.br/filters?tag=billing&tag=overdue"


def test_build_public_media_url_returns_absolute_url_unchanged():
    assert (
        build_public_media_url("https://cdn.papermoon.com.br/media/banner.png")
        == "https://cdn.papermoon.com.br/media/banner.png"
    )


def test_build_public_media_url_uses_public_base(settings):
    settings.MEDIA_PUBLIC_BASE_URL = "https://media.papermoon.com.br/"

    url = build_public_media_url("/uploads/banner.png")

    assert url == "https://media.papermoon.com.br/uploads/banner.png"


def test_build_public_media_url_uses_request_when_public_base_missing(settings):
    settings.MEDIA_PUBLIC_BASE_URL = ""
    request = Mock()
    request.build_absolute_uri.return_value = "https://api.papermoon.com.br/media/banner.png"

    url = build_public_media_url("/media/banner.png", request=request)

    assert url == "https://api.papermoon.com.br/media/banner.png"
    request.build_absolute_uri.assert_called_once_with("/media/banner.png")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://app.papermoon.com.br/dashboard", "https://app.papermoon.com.br/dashboard"),
        ("https://sub.papermoon.com.br/dashboard", "https://sub.papermoon.com.br/dashboard"),
        ("javascript:alert(1)", None),
        ("https://localhost:3000/dashboard", None),
        ("http://127.0.0.1:3000/dashboard", None),
        ("http://10.0.0.4/internal", None),
        ("https://intranet/internal", None),
    ],
)
def test_sanitize_public_url_general_cases(value, expected):
    assert sanitize_public_url(value) == expected


def test_sanitize_public_url_allows_localhost_when_enabled():
    assert (
        sanitize_public_url("http://localhost:3000/dashboard", allow_localhost=True)
        == "http://localhost:3000/dashboard"
    )


def test_sanitize_public_url_restricts_domains():
    assert (
        sanitize_public_url(
            "https://sandbox.asaas.com/c/pay-123",
            allowed_domains=("asaas.com", "asaas.com.br"),
        )
        == "https://sandbox.asaas.com/c/pay-123"
    )
    assert (
        sanitize_public_url(
            "https://evil-asaas.com/c/pay-123",
            allowed_domains=("asaas.com", "asaas.com.br"),
        )
        is None
    )


def test_sanitize_payment_url_allows_only_asaas_hosts():
    assert sanitize_payment_url("https://www.asaas.com/c/pay-123") == "https://www.asaas.com/c/pay-123"
    assert sanitize_payment_url("https://checkout.evil.com/pay-123") is None
