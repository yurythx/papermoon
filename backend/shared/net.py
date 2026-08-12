"""
Client IP resolution shared by anything that needs to key on "who is calling"
(brute-force guards, audit logging) outside of DRF's own throttle machinery.

Django is never exposed directly to the internet except the Asaas webhook
(which doesn't use IP-based throttling) — see docs/deployment.md. The BFF
(Next.js) is the sole trusted hop, and it rewrites X-Forwarded-For with the
real visitor IP before forwarding (frontend/src/lib/session.ts::getClientIp).
`NUM_PROXIES` in REST_FRAMEWORK settings tells DRF's own throttles the same
thing; this helper mirrors that exact algorithm so code outside DRF's
throttle classes (e.g. LoginAttemptGuard) agrees with it instead of trusting
X-Forwarded-For unconditionally.
"""

from django.http import HttpRequest
from rest_framework.settings import api_settings


def get_client_ip(request: HttpRequest) -> str:
    remote_addr = request.META.get("REMOTE_ADDR", "unknown")
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    num_proxies = api_settings.NUM_PROXIES

    if num_proxies is None:
        # Same fallback DRF uses when NUM_PROXIES isn't configured — trusting
        # the leftmost XFF entry is only safe if nothing else can set this
        # header, which is why NUM_PROXIES=1 is always set in base.py.
        return "".join(xff.split()) if xff else remote_addr

    if num_proxies == 0 or xff is None:
        return remote_addr

    addrs = xff.split(",")
    client_addr = addrs[-min(num_proxies, len(addrs))]
    return client_addr.strip()
