"use client";

import { useId, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { KeyRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CodeBlock } from "@/components/compound/code-block";
import { CopyButton } from "@/components/compound/copy-button";
import { EmptyState } from "@/components/compound/empty-state";
import { PageHeader } from "@/components/compound/page-header";
import { integrationService } from "@/lib/services";
import type { KeycloakIntegrationLanguage } from "@/types";

const LANGUAGES: { id: KeycloakIntegrationLanguage; label: string }[] = [
  { id: "django", label: "Django" },
  { id: "drf", label: "DRF" },
  { id: "nextjs", label: "Next.js" },
  { id: "js", label: "JS" },
  { id: "node", label: "Node.js" },
  { id: "go", label: "Go" },
  { id: "csharp", label: "C#" },
];

// Seletor de linguagem hand-rolled seguindo o mesmo padrão role="tablist" de
// src/components/marketing/pricing-tabs.tsx — não existe um primitivo de
// Tabs pronto no projeto (nenhuma lib de headless UI está instalada).
function LanguageTabs({
  value,
  onChange,
}: {
  value: KeycloakIntegrationLanguage;
  onChange: (v: KeycloakIntegrationLanguage) => void;
}) {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const tabListId = useId();

  function selectTab(index: number) {
    const normalizedIndex = (index + LANGUAGES.length) % LANGUAGES.length;
    onChange(LANGUAGES[normalizedIndex].id);
    tabRefs.current[normalizedIndex]?.focus();
  }

  return (
    <div
      role="tablist"
      aria-label="Linguagem / framework"
      className="flex flex-wrap gap-1 bg-surface-2 p-1 rounded-xl border border-border-subtle"
    >
      {LANGUAGES.map((lang, index) => (
        <button
          key={lang.id}
          id={`${tabListId}-tab-${lang.id}`}
          role="tab"
          type="button"
          aria-selected={value === lang.id}
          aria-controls={`${tabListId}-panel`}
          tabIndex={value === lang.id ? 0 : -1}
          onClick={() => onChange(lang.id)}
          onKeyDown={(event) => {
            if (event.key === "ArrowRight" || event.key === "ArrowDown") {
              event.preventDefault();
              selectTab(index + 1);
            } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
              event.preventDefault();
              selectTab(index - 1);
            } else if (event.key === "Home") {
              event.preventDefault();
              selectTab(0);
            } else if (event.key === "End") {
              event.preventDefault();
              selectTab(LANGUAGES.length - 1);
            }
          }}
          ref={(element) => {
            tabRefs.current[index] = element;
          }}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all duration-150 ${
            value === lang.id
              ? "bg-surface-0 text-text-primary shadow-sm"
              : "text-text-tertiary hover:text-text-secondary"
          }`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}

function UrlField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <label className="text-xs font-medium text-text-tertiary mb-1 block">{label}</label>
      <Input
        readOnly
        value={value}
        className="font-mono text-xs opacity-90 cursor-default"
        rightElement={<CopyButton value={value} />}
      />
    </div>
  );
}

export default function KeycloakIntegrationPage() {
  const [appName, setAppName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [language, setLanguage] = useState<KeycloakIntegrationLanguage>("nextjs");

  const { data, isFetching, isError, isFetched, refetch } = useQuery({
    queryKey: ["keycloak-integration-guide", language, appName, baseUrl],
    queryFn: () =>
      integrationService.getKeycloakGuide({ language, app_name: appName, base_url: baseUrl }),
    enabled: false,
  });

  const canGenerate = baseUrl.trim().startsWith("http");

  return (
    <div className="space-y-8">
      <PageHeader
        title="Integração SSO (Keycloak)"
        description="Gere um guia com as URLs e o código pra conectar seu sistema ao Keycloak do PaperMoon"
      />

      <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs font-medium text-text-tertiary mb-1 block">
              Nome do seu sistema
            </label>
            <Input
              placeholder="Ex: Sistema de Chamados"
              value={appName}
              onChange={(e) => setAppName(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-text-tertiary mb-1 block">
              URL base do seu sistema
            </label>
            <Input
              placeholder="https://meusistema.com.br"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-text-tertiary mb-2 block">
            Linguagem / framework
          </label>
          <LanguageTabs value={language} onChange={setLanguage} />
        </div>

        <Button
          variant="primary"
          size="sm"
          loading={isFetching}
          disabled={!canGenerate}
          onClick={() => refetch()}
        >
          Gerar guia
        </Button>
      </div>

      {isError && (
        <p className="text-sm text-danger">
          Não foi possível gerar o guia agora. Tente de novo em instantes.
        </p>
      )}

      {isFetched && data && !data.available && (
        <EmptyState
          icon={KeyRound}
          title="Integração Keycloak ainda não está disponível"
          description="Seu plano atual não inclui um realm Keycloak provisionado, ou o serviço ainda está sendo configurado pro seu contrato. Fale com a gente pra saber mais."
          action={{ label: "Falar com a equipe", href: "mailto:contato@papermoon.com.br" }}
        />
      )}

      {isFetched && data?.available && (
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            {data.verified ? (
              <Badge variant="success" dot>
                Confirmado com o Keycloak agora
              </Badge>
            ) : (
              <Badge variant="warning" dot>
                Não confirmado — usando caminhos padrão
              </Badge>
            )}
          </div>

          <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-text-primary">Valores da integração</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <UrlField label="Issuer" value={data.issuer ?? ""} />
              <UrlField label="Client ID sugerido" value={data.client_id_suggestion ?? ""} />
              <UrlField
                label="Redirect URI (cadastre este no Keycloak)"
                value={data.redirect_uri ?? ""}
              />
              <UrlField label="Scopes" value={(data.scopes ?? []).join(" ")} />
              <UrlField label="Authorization endpoint" value={data.authorization_endpoint ?? ""} />
              <UrlField label="Token endpoint" value={data.token_endpoint ?? ""} />
              <UrlField label="Userinfo endpoint" value={data.userinfo_endpoint ?? ""} />
              <UrlField label="JWKS URI" value={data.jwks_uri ?? ""} />
              <UrlField label="Logout endpoint" value={data.end_session_endpoint ?? ""} />
            </div>
          </div>

          <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-semibold text-text-primary">Passo a passo</h3>
            <ol className="space-y-2.5">
              {(data.steps ?? []).map((step, i) => (
                <li key={i} className="flex gap-3 text-sm text-text-secondary">
                  <span className="shrink-0 w-5 h-5 rounded-full bg-surface-3 text-text-tertiary text-xs font-semibold flex items-center justify-center mt-0.5">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </div>

          <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="text-sm font-semibold text-text-primary">
                Código ({data.package})
              </h3>
              <code className="bg-surface-3 px-1.5 py-0.5 rounded font-mono text-xs text-info">
                {data.install_command}
              </code>
            </div>
            <CodeBlock code={data.code_snippet ?? ""} />
          </div>
        </div>
      )}
    </div>
  );
}
