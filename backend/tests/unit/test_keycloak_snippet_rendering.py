"""
Unit tests for apps/subscriptions/keycloak_guide.py::render_code_snippet —
garante que nenhum placeholder `__ALGO__` sobra em nenhum dos 7 pacotes de
linguagem, tanto no modo guia (client_secret=None) quanto no modo criação
real (client_secret= valor de verdade).
"""

import re

import pytest

from apps.subscriptions.keycloak_guide import render_code_snippet, standard_endpoints
from apps.subscriptions.keycloak_integration_content import LANGUAGE_PACKS

_PLACEHOLDER_RE = re.compile(r"__[A-Z_]+__")

_ISSUER = "https://auth.papermoon.com/realms/tenant-abc123"
_ENDPOINTS = standard_endpoints(_ISSUER)


def _render(language: str, client_secret: str | None) -> str:
    return render_code_snippet(
        language=language,
        issuer=_ISSUER,
        client_id="minha-app",
        redirect_uri="https://meusistema.com.br/callback",
        redirect_path="/callback",
        base_url="https://meusistema.com.br",
        endpoints=_ENDPOINTS,
        client_secret=client_secret,
    )


@pytest.mark.parametrize("language", list(LANGUAGE_PACKS))
class TestRenderCodeSnippetNoLeftoverPlaceholders:
    def test_guide_mode_has_no_leftover_placeholders(self, language):
        snippet = _render(language, client_secret=None)
        leftover = _PLACEHOLDER_RE.findall(snippet)
        assert leftover == [], f"{language}: placeholders sobrando: {leftover}"

    def test_creation_mode_has_no_leftover_placeholders(self, language):
        snippet = _render(language, client_secret="real-secret-value")
        leftover = _PLACEHOLDER_RE.findall(snippet)
        assert leftover == [], f"{language}: placeholders sobrando: {leftover}"

    def test_creation_mode_embeds_real_secret(self, language):
        pack = LANGUAGE_PACKS[language]
        uses_secret = "__CLIENT_SECRET__" in pack["code_template"]
        snippet = _render(language, client_secret="real-secret-value")
        if uses_secret:
            assert "real-secret-value" in snippet
        else:
            # Client público (js) ou fluxo que não autentica como client (drf,
            # que só valida tokens) — o template nem referencia __CLIENT_SECRET__.
            assert "real-secret-value" not in snippet

    def test_guide_mode_falls_back_to_historical_placeholder_when_template_uses_secret(
        self, language
    ):
        pack = LANGUAGE_PACKS[language]
        snippet = _render(language, client_secret=None)
        if "__CLIENT_SECRET__" in pack["code_template"]:
            assert "COLE_AQUI_O_CLIENT_SECRET" in snippet
