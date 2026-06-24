"""
Brute-force protection for the login endpoint.

Tracks failed attempts per IP in Redis. After MAX_ATTEMPTS failures within
WINDOW_TTL seconds, the IP is locked out for LOCKOUT_TTL seconds.

The lockout expiry timestamp is stored as the cache value so callers can
compute Retry-After without needing a TTL query.
"""

import hashlib
import time

from django.core.cache import cache


class LoginAttemptGuard:
    MAX_ATTEMPTS = 5
    LOCKOUT_TTL = 15 * 60  # 15 minutes
    WINDOW_TTL = 10 * 60  # rolling window for counting attempts

    def __init__(self, request):
        ip = self._get_client_ip(request)
        # Hash to avoid storing raw IPs in cache and to normalize key length.
        h = hashlib.sha256(ip.encode()).hexdigest()[:16]
        self._key_attempts = f"auth:attempts:{h}"
        self._key_lockout = f"auth:lockout:{h}"

    def _get_client_ip(self, request) -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def lockout_remaining(self) -> int:
        """Return seconds remaining in the active lockout, or 0 if not locked."""
        until = cache.get(self._key_lockout)
        if until is None:
            return 0
        return max(0, int(until - time.time()))

    def record_failure(self) -> None:
        """Increment the failure counter and impose a lockout if the threshold is hit."""
        attempts: int = (cache.get(self._key_attempts) or 0) + 1
        cache.set(self._key_attempts, attempts, timeout=self.WINDOW_TTL)
        if attempts >= self.MAX_ATTEMPTS:
            cache.set(
                self._key_lockout,
                time.time() + self.LOCKOUT_TTL,
                timeout=self.LOCKOUT_TTL,
            )

    def clear(self) -> None:
        """Reset all counters on a successful login."""
        cache.delete(self._key_attempts)
        cache.delete(self._key_lockout)
