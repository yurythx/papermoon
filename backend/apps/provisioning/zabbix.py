import logging

import requests

from apps.provisioning.base import AbstractProvisioner

logger = logging.getLogger(__name__)


class ZabbixProvisioner(AbstractProvisioner):
    """
    Provisions customer access in a self-hosted Zabbix instance.

    Requires ZABBIX_API_URL and ZABBIX_API_TOKEN in settings.
    Falls back to a log-only stub when credentials are absent.

    Zabbix API docs: https://www.zabbix.com/documentation/current/en/manual/api
    Flow: create user → assign to hostgroup → enable notifications → return userid
    """

    service_key = "zabbix"

    def __init__(self) -> None:
        from django.conf import settings

        self._api_url = (getattr(settings, "ZABBIX_API_URL", "") or "").rstrip("/")
        self._api_token = getattr(settings, "ZABBIX_API_TOKEN", "") or ""
        self._enabled = bool(self._api_url and self._api_token)
        if self._enabled:
            self._session = requests.Session()
            self._session.headers.update({"Content-Type": "application/json"})

    # ------------------------------------------------------------------

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        if not self._enabled:
            logger.warning(
                "ZabbixProvisioner.provision skipped — credentials not set customer_id=%s",
                customer_id,
            )
            return f"zabbix_stub_{customer_id[:8]}"

        alias = config.get("alias", f"papermoon_{customer_id[:8]}")
        name = config.get("name", alias)
        surname = config.get("surname", "")
        password = config.get("password", self._generate_password())
        usrgrpids = config.get("usrgrpids", [])  # Zabbix user groups (e.g., monitoring team)

        resp = self._call(
            "user.create",
            {
                "alias": alias,
                "name": name,
                "surname": surname,
                "passwd": password,
                "type": 1,  # 1=Zabbix user, 2=Admin, 3=Super admin
                "usrgrps": [{"usrgrpid": gid} for gid in usrgrpids],
                "medias": self._build_medias(config),
            },
        )
        user_id = str(resp.get("userids", [f"zabbix_{customer_id[:8]}"])[0])
        logger.info(
            "ZabbixProvisioner.provision ok customer_id=%s zabbix_userid=%s",
            customer_id,
            user_id,
        )
        return user_id

    def suspend(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("ZabbixProvisioner.suspend skipped — credentials not set")
            return

        # Move user to a disabled group (usrgrpid=9 = disabled in default Zabbix)
        disabled_grpid = "9"
        self._call(
            "user.update", {"userid": external_id, "usrgrps": [{"usrgrpid": disabled_grpid}]}
        )
        logger.info("ZabbixProvisioner.suspend ok external_id=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("ZabbixProvisioner.reactivate skipped — credentials not set")
            return

        # Restore to default user group (usrgrpid=8 = Zabbix users in default install)
        default_grpid = "8"
        self._call("user.update", {"userid": external_id, "usrgrps": [{"usrgrpid": default_grpid}]})
        logger.info("ZabbixProvisioner.reactivate ok external_id=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        if not self._enabled:
            logger.warning("ZabbixProvisioner.deprovision skipped — credentials not set")
            return

        self._call("user.delete", [external_id])
        logger.info("ZabbixProvisioner.deprovision ok external_id=%s", external_id)

    # ------------------------------------------------------------------

    def _call(self, method: str, params: dict | list) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth": self._api_token,
            "id": 1,
        }
        resp = self._session.post(f"{self._api_url}/api_jsonrpc.php", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Zabbix API error: {data['error']}")
        return data.get("result", {})

    @staticmethod
    def _build_medias(config: dict) -> list[dict]:
        email = config.get("admin_email")
        if not email:
            return []
        return [
            {
                "mediatypeid": "1",  # 1 = Email in default Zabbix
                "sendto": email,
                "active": 0,
                "severity": 63,  # all severity levels
                "period": "1-7,00:00-24:00",
            }
        ]

    @staticmethod
    def _generate_password() -> str:
        import secrets

        return secrets.token_urlsafe(16)
