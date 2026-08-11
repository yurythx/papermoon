from __future__ import annotations

import logging

import requests

from apps.provisioning.base import AbstractProvisioner
from apps.provisioning.keycloak_config import open_admin_session

logger = logging.getLogger(__name__)

_TIMEOUT = 10  # segundos — nenhuma chamada aqui tinha timeout antes, corrigido de graça


class KeycloakConnectionUnavailableError(Exception):
    """A conexão central com o Keycloak não está configurada/ativa no backoffice."""


class KeycloakClientAlreadyExistsError(Exception):
    """Já existe um client com esse clientId no realm (HTTP 409)."""


class KeycloakProvisioner(AbstractProvisioner):
    """
    Provisions a Keycloak realm for a customer, and (via create_oidc_client)
    OIDC clients dentro do realm de um cliente já provisionado.

    A conexão central (api_url + admin_token) é editável em runtime pelo
    backoffice — ver apps.provisioning.keycloak_config — e resolvida a CADA
    chamada, nunca guardada em self.__init__. Isso é proposital: o registry
    (apps.provisioning.registry) guarda uma única instância desta classe num
    dict global de processo; se a config fosse lida uma vez no __init__, uma
    edição no backoffice só valeria depois de reiniciar o processo.

    Falls back to log-only stub when the central connection is absent.
    """

    service_key = "keycloak"

    def _admin(self) -> tuple[requests.Session | None, str]:
        return open_admin_session()

    def provision(self, customer_id: str, service_access_id: str, config: dict) -> str:
        session, api_url = self._admin()
        if session is None:
            logger.warning(
                "KeycloakProvisioner.provision — manual setup required customer_id=%s",
                customer_id,
            )
            return f"keycloak_stub_{customer_id[:8]}"

        realm_name = config.get("realm_name", f"tenant-{customer_id[:8]}")
        resp = session.post(
            f"{api_url}/admin/realms",
            json={
                "realm": realm_name,
                "enabled": True,
                "displayName": config.get("display_name", realm_name),
            },
            timeout=_TIMEOUT,
        )
        if resp.status_code == 409:
            logger.info("KeycloakProvisioner: realm %s already exists", realm_name)
        else:
            resp.raise_for_status()

        logger.info(
            "KeycloakProvisioner.provision ok customer_id=%s realm=%s",
            customer_id,
            realm_name,
        )
        return realm_name

    def suspend(self, external_id: str, customer_id: str) -> None:
        session, api_url = self._admin()
        if session is None:
            logger.warning(
                "KeycloakProvisioner.suspend — manual action required external_id=%s",
                external_id,
            )
            return

        resp = session.put(
            f"{api_url}/admin/realms/{external_id}",
            json={"enabled": False},
            timeout=_TIMEOUT,
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("KeycloakProvisioner.suspend ok realm=%s", external_id)

    def reactivate(self, external_id: str, customer_id: str) -> None:
        session, api_url = self._admin()
        if session is None:
            logger.warning(
                "KeycloakProvisioner.reactivate — manual action required external_id=%s",
                external_id,
            )
            return

        resp = session.put(
            f"{api_url}/admin/realms/{external_id}",
            json={"enabled": True},
            timeout=_TIMEOUT,
        )
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("KeycloakProvisioner.reactivate ok realm=%s", external_id)

    def deprovision(self, external_id: str, customer_id: str) -> None:
        session, api_url = self._admin()
        if session is None:
            logger.warning(
                "KeycloakProvisioner.deprovision — manual action required external_id=%s",
                external_id,
            )
            return

        resp = session.delete(f"{api_url}/admin/realms/{external_id}", timeout=_TIMEOUT)
        if resp.status_code not in (200, 204, 404):
            resp.raise_for_status()
        logger.info("KeycloakProvisioner.deprovision ok realm=%s", external_id)

    # --- Client OIDC (usado pela página de integração do cliente) ---

    def find_client_uuid(self, *, realm: str, client_id: str) -> str | None:
        """Retorna o id interno (UUID) do Keycloak pra um clientId, ou None se
        não existir. Levanta KeycloakConnectionUnavailableError se a conexão
        central não estiver ativa — diferente dos métodos de ciclo de vida
        acima, aqui não faz sentido degradar silenciosamente pra stub, porque
        quem chama precisa de uma resposta real pra decidir o próximo passo."""
        session, api_url = self._admin()
        if session is None:
            raise KeycloakConnectionUnavailableError()

        resp = session.get(
            f"{api_url}/admin/realms/{realm}/clients",
            params={"clientId": client_id, "exact": "true"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        return results[0]["id"]

    def get_client_secret(self, *, realm: str, kc_uuid: str) -> str:
        session, api_url = self._admin()
        if session is None:
            raise KeycloakConnectionUnavailableError()

        resp = session.get(
            f"{api_url}/admin/realms/{realm}/clients/{kc_uuid}/client-secret",
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["value"]

    def create_oidc_client(
        self,
        *,
        realm: str,
        client_id: str,
        name: str,
        redirect_uris: list[str],
        web_origins: list[str],
        public_client: bool,
        base_url: str = "",
    ) -> dict:
        """Cria um client OIDC de verdade no realm do cliente via Admin REST
        API. Retorna {"kc_uuid", "client_id", "client_secret"} — client_secret
        é None quando public_client=True (client público não tem segredo).

        Levanta KeycloakConnectionUnavailableError (conexão central fora do ar) ou
        KeycloakClientAlreadyExistsError (409 — já existe um client com esse
        clientId) em vez de fingir sucesso: devolver credenciais falsas pro
        cliente seria pior que um erro."""
        session, api_url = self._admin()
        if session is None:
            raise KeycloakConnectionUnavailableError()

        attributes: dict[str, str] = {"post.logout.redirect.uris": f"{base_url}/*"}
        if public_client:
            attributes["pkce.code.challenge.method"] = "S256"

        payload = {
            "clientId": client_id,
            "name": name,
            "protocol": "openid-connect",
            "enabled": True,
            "publicClient": public_client,
            "standardFlowEnabled": True,
            "implicitFlowEnabled": False,
            "directAccessGrantsEnabled": False,
            "serviceAccountsEnabled": False,
            "redirectUris": redirect_uris,
            "webOrigins": web_origins if public_client else [],
            "rootUrl": base_url,
            "frontchannelLogout": True,
            "attributes": attributes,
        }
        if not public_client:
            payload["clientAuthenticatorType"] = "client-secret"

        resp = session.post(
            f"{api_url}/admin/realms/{realm}/clients",
            json=payload,
            timeout=_TIMEOUT,
        )
        if resp.status_code == 409:
            raise KeycloakClientAlreadyExistsError(client_id)
        resp.raise_for_status()

        location = resp.headers.get("Location", "")
        kc_uuid = location.rstrip("/").rsplit("/", 1)[-1] if location else None
        if not kc_uuid:
            kc_uuid = self.find_client_uuid(realm=realm, client_id=client_id)
        if not kc_uuid:
            # Extremamente improvável (o POST deu certo mas não conseguimos
            # localizar o client criado) — melhor falhar alto do que devolver
            # um resultado incompleto.
            raise RuntimeError(
                f"Client '{client_id}' criado no Keycloak mas não foi possível localizar seu id."
            )

        client_secret = None
        if not public_client:
            client_secret = self.get_client_secret(realm=realm, kc_uuid=kc_uuid)

        logger.info(
            "KeycloakProvisioner.create_oidc_client ok realm=%s client_id=%s public=%s",
            realm,
            client_id,
            public_client,
        )
        return {"kc_uuid": kc_uuid, "client_id": client_id, "client_secret": client_secret}
