import logging

from django.conf import settings
import requests

logger = logging.getLogger(__name__)


class ChatwootClient:
    def __init__(self) -> None:
        self._base_url = settings.CHATWOOT_API_URL.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "api_access_token": settings.CHATWOOT_API_KEY,
                "Content-Type": "application/json",
            }
        )

    def suspend_agents(self, customer_id: str) -> bool:
        try:
            response = self._session.post(
                f"{self._base_url}/api/v1/profile/suspend",
                json={"customer_id": customer_id},
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.error("ChatwootClient.suspend_agents customer_id=%s error=%s", customer_id, exc)
            raise

    def reactivate_agents(self, customer_id: str) -> bool:
        try:
            response = self._session.post(
                f"{self._base_url}/api/v1/profile/reactivate",
                json={"customer_id": customer_id},
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            logger.error(
                "ChatwootClient.reactivate_agents customer_id=%s error=%s", customer_id, exc
            )
            raise

    def provision_customer(self, customer_id: str) -> dict:
        try:
            response = self._session.post(
                f"{self._base_url}/api/v1/accounts",
                json={"customer_id": customer_id},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error(
                "ChatwootClient.provision_customer customer_id=%s error=%s", customer_id, exc
            )
            raise
