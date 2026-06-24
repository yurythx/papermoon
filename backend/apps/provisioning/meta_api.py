import logging

import requests

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)

_GRAPH_URL = "https://graph.facebook.com/v19.0"


class MetaWhatsAppProvisioner(AbstractProvisioner):
    """
    Provisions customer access via Meta WhatsApp Business API (Cloud API).

    Requires META_WHATSAPP_TOKEN and META_WABA_ID in settings.
    Falls back to a log-only stub when credentials are absent.

    Meta Cloud API docs: https://developers.facebook.com/docs/whatsapp/cloud-api
    Flow: register phone number → subscribe to webhooks → return phone_number_id as external_id
    """

    service_key = "meta_whatsapp"

    def __init__(self) -> None:
        from django.conf import settings

        self._token = getattr(settings, "META_WHATSAPP_TOKEN", "") or ""
        self._waba_id = getattr(settings, "META_WABA_ID", "") or ""
        self._enabled = bool(self._token and self._waba_id)
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update(
                {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
            )

    # ------------------------------------------------------------------

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "MetaWhatsAppProvisioner.provision skipped — credentials not set customer_id=%s",
                customer_id,
            )
            return f"waba_stub_{customer_id[:8]}"

        # Retrieve available phone numbers under the WABA and assign the first unregistered one.
        # In production, config should carry the specific phone_number_id to register.
        phone_number_id = config.get("phone_number_id")
        if not phone_number_id:
            phone_number_id = self._pick_phone_number()

        if not phone_number_id:
            raise RuntimeError(
                f"No available phone number in WABA {self._waba_id} for customer {customer_id}"
            )

        # Register the number so it can send/receive messages
        resp = self._session.post(
            f"{_GRAPH_URL}/{phone_number_id}/register",
            json={"messaging_product": "whatsapp", "pin": config.get("pin", "000000")},
        )
        resp.raise_for_status()
        logger.info(
            "MetaWhatsAppProvisioner.provision ok customer_id=%s phone_number_id=%s",
            customer_id,
            phone_number_id,
        )
        return str(phone_number_id)

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("MetaWhatsAppProvisioner.suspend skipped — credentials not set")
            return

        # Deregister makes the number unable to send/receive without deleting it
        resp = self._session.post(
            f"{_GRAPH_URL}/{external_id}/deregister",
            json={"messaging_product": "whatsapp"},
        )
        if resp.status_code not in (200, 404):
            resp.raise_for_status()
        logger.info("MetaWhatsAppProvisioner.suspend ok external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("MetaWhatsAppProvisioner.reactivate skipped — credentials not set")
            return

        resp = self._session.post(
            f"{_GRAPH_URL}/{external_id}/register",
            json={"messaging_product": "whatsapp"},
        )
        if resp.status_code not in (200, 404):
            resp.raise_for_status()
        logger.info("MetaWhatsAppProvisioner.reactivate ok external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("MetaWhatsAppProvisioner.deprovision skipped — credentials not set")
            return

        # Deregister is the closest to "remove" — Meta doesn't allow deleting phone numbers
        # via API once they've been verified.
        resp = self._session.post(
            f"{_GRAPH_URL}/{external_id}/deregister",
            json={"messaging_product": "whatsapp"},
        )
        if resp.status_code not in (200, 404):
            resp.raise_for_status()
        logger.info("MetaWhatsAppProvisioner.deprovision ok external_id=%s", external_id)

    # ------------------------------------------------------------------

    def _pick_phone_number(self) -> str | None:
        """Return the first unregistered phone number under the WABA."""
        resp = self._session.get(
            f"{_GRAPH_URL}/{self._waba_id}/phone_numbers",
            params={"fields": "id,verified_name,code_verification_status"},
        )
        resp.raise_for_status()
        numbers = resp.json().get("data", [])
        for number in numbers:
            if number.get("code_verification_status") != "VERIFIED":
                return number["id"]
        # All numbers already verified/in use — return None and let the caller decide
        return None
