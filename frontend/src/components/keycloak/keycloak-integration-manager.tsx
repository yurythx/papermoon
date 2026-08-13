"use client";

import { useId, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";
import { CheckCircle2, Eye, EyeOff, KeyRound, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { CodeBlock } from "@/components/compound/code-block";
import { CopyButton } from "@/components/compound/copy-button";
import { EmptyState } from "@/components/compound/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { cardClass } from "@/components/ui/card";
import type {
  KeycloakClientIntegration,
  KeycloakIntegrationCreatePayload,
  KeycloakIntegrationCreateResult,
  KeycloakIntegrationGuide,
  KeycloakIntegrationLanguage,
  KeycloakIntegrationListResult,
  KeycloakIntegrationSecretResult,
} from "@/types";

const LANGUAGES: { id: KeycloakIntegrationLanguage; label: string }[] = [
  { id: "django", label: "Django" },
  { id: "drf", label: "DRF" },
  { id: "nextjs", label: "Next.js" },
  { id: "js", label: "JS" },
  { id: "node", label: "Node.js" },
  { id: "go", label: "Go" },
  { id: "csharp", label: "C#" },
];

/** Contrato mínimo que a página precisa fornecer — client-facing (em nome de
 * quem está logado) e admin-facing (staff em nome de um cliente escolhido)
 * implementam isso apontando pros endpoints certos, o resto da UI/lógica é
 * 100% compartilhado. */
export interface KeycloakIntegrationServices {
  listIntegrations: () => Promise<KeycloakIntegrationListResult>;
  createIntegration: (
    payload: KeycloakIntegrationCreatePayload
  ) => Promise<KeycloakIntegrationCreateResult>;
  getGuide: (params: {
    language: KeycloakIntegrationLanguage;
    app_name: string;
    base_url: string;
  }) => Promise<KeycloakIntegrationGuide>;
  getSecret: (integrationId: string) => Promise<KeycloakIntegrationSecretResult>;
}

// Seletor de linguagem hand-rolled seguindo o mesmo padrão role="tablist" de
// src/components/marketing/pricing-tabs.tsx — não existe um primitivo de
// Tabs pronto no projeto (nenhuma lib de headless UI está instalada).
export function LanguageTabs({
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

function SecretField({ value }: { value: string }) {
  const [visible, setVisible] = useState(false);
  return (
    <div>
      <label className="text-xs font-medium text-text-tertiary mb-1 block">Client Secret</label>
      <Input
        readOnly
        type={visible ? "text" : "password"}
        value={value}
        className="font-mono text-xs opacity-90 cursor-default pr-16"
        rightElement={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setVisible((v) => !v)}
              aria-label={visible ? "Ocultar client secret" : "Mostrar client secret"}
              className="rounded-sm text-text-tertiary hover:text-text-secondary transition-colors cursor-pointer"
            >
              {visible ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
            <CopyButton value={value} />
          </div>
        }
      />
    </div>
  );
}

function ExistingIntegrationRow({
  integration,
  getSecret,
}: {
  integration: KeycloakClientIntegration;
  getSecret: (integrationId: string) => Promise<KeycloakIntegrationSecretResult>;
}) {
  const [secret, setSecret] = useState<string | null>(null);

  const secretMutation = useMutation({
    mutationFn: () => getSecret(integration.id),
    onSuccess: (result) => setSecret(result.client_secret),
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao buscar credenciais.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  return (
    <div className={cardClass({ className: "space-y-3" })}>
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <p className="text-sm font-semibold text-text-primary">{integration.app_name}</p>
          <p className="text-xs text-text-tertiary font-mono mt-0.5">{integration.client_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="muted">
            {LANGUAGES.find((l) => l.id === integration.language)?.label ?? integration.language}
          </Badge>
          {integration.public_client ? (
            <Badge variant="info">Público (PKCE)</Badge>
          ) : (
            <Badge variant="default">Confidencial</Badge>
          )}
        </div>
      </div>

      {!integration.public_client && (
        <>
          {secret ? (
            <SecretField value={secret} />
          ) : (
            <Button
              variant="secondary"
              size="sm"
              loading={secretMutation.isPending}
              onClick={() => secretMutation.mutate()}
            >
              Ver credenciais
            </Button>
          )}
        </>
      )}
    </div>
  );
}

function IntegrationResultDetails({ result }: { result: KeycloakIntegrationCreateResult }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 flex-wrap">
        {result.verified ? (
          <Badge variant="success" dot>
            Confirmado com o Keycloak agora
          </Badge>
        ) : (
          <Badge variant="warning" dot>
            Não confirmado — usando caminhos padrão
          </Badge>
        )}
        {result.public_client ? (
          <Badge variant="info">Client público — PKCE, sem secret</Badge>
        ) : (
          <Badge variant="default">Client confidencial</Badge>
        )}
      </div>

      <div className={cardClass({ className: "space-y-4" })}>
        <h3 className="text-sm font-semibold text-text-primary">Credenciais da integração</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <UrlField label="Issuer" value={result.issuer} />
          <UrlField label="Client ID" value={result.client_id} />
          {result.client_secret && <SecretField value={result.client_secret} />}
          <UrlField label="Redirect URI (já cadastrado no Keycloak)" value={result.redirect_uri} />
          <UrlField label="Scopes" value={result.scopes.join(" ")} />
          <UrlField label="Authorization endpoint" value={result.authorization_endpoint} />
          <UrlField label="Token endpoint" value={result.token_endpoint} />
          <UrlField label="Userinfo endpoint" value={result.userinfo_endpoint} />
          <UrlField label="JWKS URI" value={result.jwks_uri} />
          <UrlField label="Logout endpoint" value={result.end_session_endpoint} />
        </div>
      </div>

      <div className={cardClass({ className: "space-y-4" })}>
        <h3 className="text-sm font-semibold text-text-primary">Passo a passo</h3>
        <ol className="space-y-2.5">
          {result.steps.map((step, i) => (
            <li key={i} className="flex gap-3 text-sm text-text-secondary">
              <span className="shrink-0 w-5 h-5 rounded-full bg-surface-3 text-text-tertiary text-xs font-semibold flex items-center justify-center mt-0.5">
                {i + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </div>

      <div className={cardClass({ className: "space-y-4" })}>
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h3 className="text-sm font-semibold text-text-primary">Código ({result.package})</h3>
          <code className="bg-surface-3 px-1.5 py-0.5 rounded font-mono text-xs text-info">
            {result.install_command}
          </code>
        </div>
        <CodeBlock code={result.code_snippet} />
      </div>
    </div>
  );
}

interface UnavailableCopy {
  title: string;
  description: string;
  action?: { label: string; href: string };
}

// Cópia padrão (client-facing): NUNCA expõe o motivo técnico real — nem
// sempre "a conexão central não está configurada" é algo que o cliente
// deveria saber (parece um problema do plano dele, quando é da plataforma).
// A página admin passa uma `unavailable` própria, sensível ao `reason`
// exato, porque ali é staff tentando resolver o problema.
function defaultUnavailableCopy(): UnavailableCopy {
  return {
    title: "Integração Keycloak ainda não está disponível",
    description:
      "Seu plano atual não inclui um realm Keycloak provisionado, ou o serviço ainda está sendo configurado pro seu contrato. Fale com a gente pra saber mais.",
    action: { label: "Falar com a equipe", href: "mailto:contato@papermoon.cloud" },
  };
}

export function KeycloakIntegrationManager({
  services,
  queryKeyPrefix,
  getUnavailableCopy = defaultUnavailableCopy,
}: {
  services: KeycloakIntegrationServices;
  /** Prefixo único de cache do React Query — precisa diferenciar por cliente
   * na página admin (várias instâncias na mesma sessão, um cliente por vez),
   * senão trocar de cliente mostraria dados cacheados do cliente anterior. */
  queryKeyPrefix: readonly unknown[];
  /** Cópia mostrada quando a integração não está disponível, a partir do
   * `reason` ("platform_not_configured" | "no_service_access" | null).
   * Default é seguro pra cliente final (ignora o reason, nunca expõe o
   * motivo técnico) — a página admin passa uma versão sensível ao reason. */
  getUnavailableCopy?: (reason: string | null) => UnavailableCopy;
}) {
  const queryClient = useQueryClient();
  const [appName, setAppName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [language, setLanguage] = useState<KeycloakIntegrationLanguage>("nextjs");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [createdResult, setCreatedResult] = useState<KeycloakIntegrationCreateResult | null>(null);
  const titleId = useId();
  const descriptionId = useId();

  const { data: list, isLoading: isListLoading } = useQuery({
    queryKey: [...queryKeyPrefix, "list"],
    queryFn: services.listIntegrations,
  });

  const {
    data: guide,
    isFetching: isGuideFetching,
    isError: isGuideError,
    isFetched: isGuideFetched,
    refetch: refetchGuide,
  } = useQuery({
    queryKey: [...queryKeyPrefix, "guide", language, appName, baseUrl],
    queryFn: () => services.getGuide({ language, app_name: appName, base_url: baseUrl }),
    enabled: false,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      services.createIntegration({ language, app_name: appName, base_url: baseUrl }),
    onSuccess: (result) => {
      setCreatedResult(result);
      setConfirmOpen(false);
      queryClient.invalidateQueries({ queryKey: [...queryKeyPrefix, "list"] });
      toast.success("Integração criada — client OIDC de verdade no Keycloak.");
    },
    onError: (err) => {
      setConfirmOpen(false);
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao criar a integração.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const canGenerate = baseUrl.trim().startsWith("http");

  if (isListLoading) {
    return <Skeleton className="h-64 w-full rounded-xl" />;
  }

  if (list && !list.available) {
    const copy = getUnavailableCopy(list.reason);
    return <EmptyState icon={KeyRound} title={copy.title} description={copy.description} action={copy.action} />;
  }

  return (
    <div className="space-y-8">
      {list && list.integrations.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-text-primary">Integrações existentes</h3>
          <div className="space-y-3">
            {list.integrations.map((integration) => (
              <ExistingIntegrationRow
                key={integration.id}
                integration={integration}
                getSecret={services.getSecret}
              />
            ))}
          </div>
        </div>
      )}

      <div className={cardClass({ className: "space-y-5" })}>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs font-medium text-text-tertiary mb-1 block">
              Nome do sistema
            </label>
            <Input
              placeholder="Ex: Sistema de Chamados"
              value={appName}
              onChange={(e) => setAppName(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs font-medium text-text-tertiary mb-1 block">
              URL base do sistema
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

        <div className="flex items-center gap-3 flex-wrap">
          <Button
            variant="primary"
            size="sm"
            disabled={!canGenerate}
            onClick={() => setConfirmOpen(true)}
          >
            Criar integração
          </Button>
          <Button
            variant="secondary"
            size="sm"
            loading={isGuideFetching}
            disabled={!canGenerate}
            onClick={() => refetchGuide()}
          >
            Gerar guia
          </Button>
          <span className="text-xs text-text-tertiary">
            &quot;Criar integração&quot; cria o client de verdade no Keycloak. &quot;Gerar guia&quot;
            só mostra como fazer, sem criar nada.
          </span>
        </div>
      </div>

      {confirmOpen && (
        <Dialog
          onClose={() => setConfirmOpen(false)}
          titleId={titleId}
          descriptionId={descriptionId}
          className="max-w-sm p-6"
        >
          <h3 id={titleId} className="text-base font-semibold text-text-primary">
            Criar integração de verdade?
          </h3>
          <p id={descriptionId} className="text-sm text-text-secondary mt-1 mb-5">
            Isso cria um client OIDC de verdade no Keycloak, dentro do realm correspondente. As
            credenciais (client_id/client_secret) aparecem logo em seguida.
          </p>
          <div className="flex gap-3 justify-end">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setConfirmOpen(false)}
              disabled={createMutation.isPending}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              Criar
            </Button>
          </div>
        </Dialog>
      )}

      {createdResult && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-success text-sm font-medium">
            <CheckCircle2 size={16} />
            Integração criada com sucesso
          </div>
          <IntegrationResultDetails result={createdResult} />
        </div>
      )}

      {isGuideError && (
        <p className="text-sm text-danger">
          Não foi possível gerar o guia agora. Tente de novo em instantes.
        </p>
      )}

      {isGuideFetched && guide && !guide.available && (() => {
        const copy = getUnavailableCopy(guide.reason ?? null);
        return <EmptyState icon={KeyRound} title={copy.title} description={copy.description} action={copy.action} />;
      })()}

      {isGuideFetched && guide?.available && (
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <ShieldCheck size={14} className="text-text-tertiary" />
            <span className="text-xs text-text-tertiary">Guia gerado — nada foi criado no Keycloak</span>
          </div>
          <div className="flex items-center gap-2">
            {guide.verified ? (
              <Badge variant="success" dot>
                Confirmado com o Keycloak agora
              </Badge>
            ) : (
              <Badge variant="warning" dot>
                Não confirmado — usando caminhos padrão
              </Badge>
            )}
          </div>

          <div className={cardClass({ className: "space-y-4" })}>
            <h3 className="text-sm font-semibold text-text-primary">Valores da integração</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <UrlField label="Issuer" value={guide.issuer ?? ""} />
              <UrlField label="Client ID sugerido" value={guide.client_id_suggestion ?? ""} />
              <UrlField
                label="Redirect URI (cadastre este no Keycloak)"
                value={guide.redirect_uri ?? ""}
              />
              <UrlField label="Scopes" value={(guide.scopes ?? []).join(" ")} />
              <UrlField label="Authorization endpoint" value={guide.authorization_endpoint ?? ""} />
              <UrlField label="Token endpoint" value={guide.token_endpoint ?? ""} />
              <UrlField label="Userinfo endpoint" value={guide.userinfo_endpoint ?? ""} />
              <UrlField label="JWKS URI" value={guide.jwks_uri ?? ""} />
              <UrlField label="Logout endpoint" value={guide.end_session_endpoint ?? ""} />
            </div>
          </div>

          <div className={cardClass({ className: "space-y-4" })}>
            <h3 className="text-sm font-semibold text-text-primary">Passo a passo</h3>
            <ol className="space-y-2.5">
              {(guide.steps ?? []).map((step, i) => (
                <li key={i} className="flex gap-3 text-sm text-text-secondary">
                  <span className="shrink-0 w-5 h-5 rounded-full bg-surface-3 text-text-tertiary text-xs font-semibold flex items-center justify-center mt-0.5">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </div>

          <div className={cardClass({ className: "space-y-4" })}>
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="text-sm font-semibold text-text-primary">
                Código ({guide.package})
              </h3>
              <code className="bg-surface-3 px-1.5 py-0.5 rounded font-mono text-xs text-info">
                {guide.install_command}
              </code>
            </div>
            <CodeBlock code={guide.code_snippet ?? ""} />
          </div>
        </div>
      )}
    </div>
  );
}
