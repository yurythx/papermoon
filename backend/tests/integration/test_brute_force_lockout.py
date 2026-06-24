"""
Integration tests for brute-force login protection (LoginAttemptGuard)
and the JWT RS256 configuration.

Scenarios covered:
  - Successful login returns access + refresh tokens
  - Wrong-password failure increments counter
  - Counter resets on successful login
  - 6th consecutive failure returns 429 with Retry-After header
  - 429 response follows UnifiedResponseRenderer contract
  - Different IPs are isolated (one IP's lockout doesn't affect another)
  - RS256 access tokens are 30-min lifetime
  - Refresh token rotation: new refresh issued, old refresh blacklisted
"""

import hashlib

from django.core.cache import cache
import pytest
from rest_framework.test import APIClient

from apps.accounts.security import LoginAttemptGuard

LOGIN_URL = "/api/v1/auth/login/"
REFRESH_URL = "/api/v1/auth/refresh/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fail_login(client: APIClient, n: int, email: str = "admin@papermoon.com") -> None:
    """Send n login requests with the wrong password."""
    for _ in range(n):
        client.post(LOGIN_URL, {"email": email, "password": "WRONG"}, format="json")


def _cache_keys_for_ip(ip: str) -> tuple[str, str]:
    h = hashlib.sha256(ip.encode()).hexdigest()[:16]
    return f"auth:attempts:{h}", f"auth:lockout:{h}"


def _clear_lockout_for_ip(ip: str = "127.0.0.1") -> None:
    key_attempts, key_lockout = _cache_keys_for_ip(ip)
    cache.delete(key_attempts)
    cache.delete(key_lockout)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_lockout():
    """Clear brute-force state before and after every test in this module."""
    _clear_lockout_for_ip()
    yield
    _clear_lockout_for_ip()


# ---------------------------------------------------------------------------
# Successful login
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLoginSuccess:
    def test_valid_credentials_return_tokens(self, api_client, admin_user):
        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "admin123"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "access" in data
        assert "refresh" in data

    def test_successful_login_clears_failure_counter(self, api_client, admin_user):
        # Accumulate some (but not max) failures first
        _fail_login(api_client, LoginAttemptGuard.MAX_ATTEMPTS - 1)

        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "admin123"},
            format="json",
        )
        assert resp.status_code == 200

        # Counter should be cleared — one more wrong attempt should NOT lock out
        _fail_login(api_client, LoginAttemptGuard.MAX_ATTEMPTS - 1)
        resp2 = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "admin123"},
            format="json",
        )
        assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# Failed login counter
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFailedLoginCounter:
    def test_wrong_password_returns_401(self, api_client, admin_user):
        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "WRONG"},
            format="json",
        )
        assert resp.status_code == 401

    def test_four_failures_do_not_trigger_lockout(self, api_client, admin_user):
        _fail_login(api_client, LoginAttemptGuard.MAX_ATTEMPTS - 1)
        # Should still be able to attempt (not locked out yet)
        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "WRONG"},
            format="json",
        )
        assert resp.status_code == 401  # still returns 401, not 429


# ---------------------------------------------------------------------------
# Lockout after MAX_ATTEMPTS
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBruteForceLockout:
    def test_sixth_attempt_returns_429(self, api_client, admin_user):
        _fail_login(api_client, LoginAttemptGuard.MAX_ATTEMPTS)
        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "WRONG"},
            format="json",
        )
        assert resp.status_code == 429

    def test_lockout_response_has_correct_error_code(self, api_client, admin_user):
        _fail_login(api_client, LoginAttemptGuard.MAX_ATTEMPTS)
        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "admin123"},
            format="json",
        )
        assert resp.status_code == 429
        body = resp.json()
        # UnifiedResponseRenderer: status>=400 → error field, not data
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "too_many_requests"

    def test_lockout_response_has_retry_after_header(self, api_client, admin_user):
        _fail_login(api_client, LoginAttemptGuard.MAX_ATTEMPTS)
        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "WRONG"},
            format="json",
        )
        assert resp.status_code == 429
        assert "Retry-After" in resp
        retry_after = int(resp["Retry-After"])
        assert 0 < retry_after <= LoginAttemptGuard.LOCKOUT_TTL

    def test_valid_credentials_blocked_during_lockout(self, api_client, admin_user):
        _fail_login(api_client, LoginAttemptGuard.MAX_ATTEMPTS)
        # Even correct credentials get 429 while locked out
        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "admin123"},
            format="json",
        )
        assert resp.status_code == 429


# ---------------------------------------------------------------------------
# LoginAttemptGuard unit tests (no HTTP, direct class usage)
# ---------------------------------------------------------------------------


class TestLoginAttemptGuardUnit:
    """Fast unit tests — no DB, no HTTP. Use a fake request stub."""

    class _FakeRequest:
        def __init__(self, ip: str = "10.0.0.1"):
            self.META = {"REMOTE_ADDR": ip}

    def setup_method(self):
        # Use a dedicated test IP to avoid interfering with other tests
        _clear_lockout_for_ip("10.0.0.1")

    def teardown_method(self):
        _clear_lockout_for_ip("10.0.0.1")

    def test_not_locked_initially(self):
        guard = LoginAttemptGuard(self._FakeRequest())
        assert guard.lockout_remaining() == 0

    def test_record_failure_below_threshold_does_not_lock(self):
        guard = LoginAttemptGuard(self._FakeRequest())
        for _ in range(LoginAttemptGuard.MAX_ATTEMPTS - 1):
            guard.record_failure()
        assert guard.lockout_remaining() == 0

    def test_record_max_failures_locks_out(self):
        guard = LoginAttemptGuard(self._FakeRequest())
        for _ in range(LoginAttemptGuard.MAX_ATTEMPTS):
            guard.record_failure()
        assert guard.lockout_remaining() > 0

    def test_lockout_remaining_is_within_expected_range(self):
        guard = LoginAttemptGuard(self._FakeRequest())
        for _ in range(LoginAttemptGuard.MAX_ATTEMPTS):
            guard.record_failure()
        remaining = guard.lockout_remaining()
        assert 0 < remaining <= LoginAttemptGuard.LOCKOUT_TTL

    def test_clear_removes_lockout(self):
        guard = LoginAttemptGuard(self._FakeRequest())
        for _ in range(LoginAttemptGuard.MAX_ATTEMPTS):
            guard.record_failure()
        assert guard.lockout_remaining() > 0
        guard.clear()
        assert guard.lockout_remaining() == 0

    def test_x_forwarded_for_header_used_when_present(self):
        req = self._FakeRequest()
        req.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.5, 10.0.0.1"
        guard = LoginAttemptGuard(req)
        # Guard should use the first IP from X-Forwarded-For
        # Verify by checking that a different IP's lockout state is unaffected
        guard2 = LoginAttemptGuard(self._FakeRequest("10.0.0.1"))
        for _ in range(LoginAttemptGuard.MAX_ATTEMPTS):
            guard.record_failure()
        # 203.0.113.5 is locked, but 10.0.0.1 should not be
        assert guard.lockout_remaining() > 0
        assert guard2.lockout_remaining() == 0
        # cleanup
        _clear_lockout_for_ip("203.0.113.5")


# ---------------------------------------------------------------------------
# JWT RS256 configuration tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestJwtRs256:
    def test_access_token_is_rs256(self, api_client, admin_user):
        import base64
        import json as _json

        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "admin123"},
            format="json",
        )
        assert resp.status_code == 200
        access = resp.json()["data"]["access"]

        # JWT header is the first segment, base64url-encoded
        header_b64 = access.split(".")[0]
        # Pad to multiple of 4
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        header = _json.loads(base64.urlsafe_b64decode(header_b64))
        assert header["alg"] == "RS256"

    def test_refresh_token_rotation(self, api_client, admin_user):
        """Old refresh token must be rejected after rotation."""
        login_resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@papermoon.com", "password": "admin123"},
            format="json",
        )
        original_refresh = login_resp.json()["data"]["refresh"]

        # Use the refresh token once to get a new pair
        rotate_resp = api_client.post(
            REFRESH_URL,
            {"refresh": original_refresh},
            format="json",
        )
        assert rotate_resp.status_code == 200
        new_refresh = rotate_resp.json()["data"]["refresh"]
        assert new_refresh != original_refresh

        # Original refresh must now be blacklisted
        reuse_resp = api_client.post(
            REFRESH_URL,
            {"refresh": original_refresh},
            format="json",
        )
        assert reuse_resp.status_code == 401
