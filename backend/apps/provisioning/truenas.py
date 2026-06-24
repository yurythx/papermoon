import logging
from urllib.parse import quote

import requests

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class TrueNASProvisioner(AbstractProvisioner):
    """
    Provisions customer storage space on a self-hosted TrueNAS instance.

    Requires TRUENAS_API_URL and TRUENAS_API_KEY in settings.
    Falls back to a log-only stub when credentials are absent.

    TrueNAS SCALE REST API: https://<host>/api/v2.0/
    Flow: create dataset → create local user → create SMB share → return user_id
    """

    service_key = "truenas"

    def __init__(self) -> None:
        from django.conf import settings

        self._base_url = (getattr(settings, "TRUENAS_API_URL", "") or "").rstrip("/")
        self._api_key = getattr(settings, "TRUENAS_API_KEY", "") or ""
        self._pool = getattr(settings, "TRUENAS_POOL", "data") or "data"
        self._enabled = bool(self._base_url and self._api_key)
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update(
                {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }
            )

    # ------------------------------------------------------------------

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "TrueNASProvisioner.provision skipped — credentials not set customer_id=%s",
                customer_id,
            )
            return f"truenas-pending-{customer_id[:8]}"

        slug = f"papermoon_{customer_id[:8]}"
        dataset_name = f"{self._pool}/{slug}"

        # 1. Create ZFS dataset
        resp = self._session.post(
            f"{self._base_url}/api/v2.0/pool/dataset",
            json={
                "name": dataset_name,
                "type": "FILESYSTEM",
                "comments": f"PaperMoon customer {customer_id}",
            },
        )
        resp.raise_for_status()

        # 2. Create local user
        password = config.get("password", self._generate_password(customer_id))
        resp = self._session.post(
            f"{self._base_url}/api/v2.0/user",
            json={
                "username": slug,
                "full_name": config.get("company_name", slug),
                "email": config.get("admin_email", f"{slug}@tenants.papermoon.com"),
                "password": password,
                "group_create": True,
                "shell": "/usr/sbin/nologin",
                "home": f"/mnt/{dataset_name}",
                "home_create": False,
            },
        )
        resp.raise_for_status()
        user_id = resp.json().get("id", slug)

        # 3. Create SMB share pointing to the dataset
        self._session.post(
            f"{self._base_url}/api/v2.0/sharing/smb",
            json={
                "path": f"/mnt/{dataset_name}",
                "name": slug,
                "comment": f"PaperMoon — {config.get('company_name', customer_id[:8])}",
            },
        )
        # SMB share creation failure is non-fatal — admin can add manually.

        logger.info(
            "TrueNASProvisioner.provision ok customer_id=%s user_id=%s dataset=%s",
            customer_id,
            user_id,
            dataset_name,
        )
        return str(user_id)

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("TrueNASProvisioner.suspend skipped — credentials not set")
            return

        resp = self._session.put(
            f"{self._base_url}/api/v2.0/user/id/{external_id}",
            json={"locked": True},
        )
        if resp.status_code not in (200, 404):
            resp.raise_for_status()
        logger.info("TrueNASProvisioner.suspend ok external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("TrueNASProvisioner.reactivate skipped — credentials not set")
            return

        resp = self._session.put(
            f"{self._base_url}/api/v2.0/user/id/{external_id}",
            json={"locked": False},
        )
        if resp.status_code not in (200, 404):
            resp.raise_for_status()
        logger.info("TrueNASProvisioner.reactivate ok external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("TrueNASProvisioner.deprovision skipped — credentials not set")
            return

        # Delete user first so the dataset is not in use
        resp = self._session.delete(f"{self._base_url}/api/v2.0/user/id/{external_id}")
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()

        slug = f"papermoon_{customer_id[:8]}"
        dataset_id = f"{self._pool}/{slug}"
        resp = self._session.delete(
            f"{self._base_url}/api/v2.0/pool/dataset/id/{quote(dataset_id, safe='')}",
            json={"recursive": True, "force": False},
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("TrueNASProvisioner.deprovision ok external_id=%s", external_id)

    @staticmethod
    def _generate_password(customer_id: str) -> str:
        import secrets

        return secrets.token_urlsafe(16)
