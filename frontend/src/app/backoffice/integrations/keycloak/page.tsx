"use client";

import { useId, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";
import { CheckCircle2, Search, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/compound/page-header";
import { CodeBlock } from "@/components/compound/code-block";
import { CopyButton } from "@/components/compound/copy-button";
import {
  KeycloakIntegrationManager,
  LanguageTabs,
} from "@/components/keycloak/keycloak-integration-manager";
import { adminService } from "@/lib/services";
import { cn } from "@/lib/utils";
import type {
  KeycloakCodeSnippetResult,
  KeycloakIntegrationLanguage,
  KeycloakIssuerValidationResult,
} from "@/types";

/* ── Validador genérico de issuer, sem vínculo com cliente nenhum ────── */

const ENDPOINT_INFO: Record<
  "issuer" | "authorization_endpoint" | "token_endpoint" | "userinfo_endpoint" | "jwks_uri" | "end_session_endpoint",
  { label: string; purpose: string; whereToUse: string }
> = {
  issuer: {
    label: "Issuer",
    purpose:
      "Identifica o realm de forma única — precisa bater exatamente com a claim \"iss\" dentro do token.",
    whereToUse:
      "Campo \"Issuer\" / \"Authority\" da sua lib OIDC. Costuma ser o único campo que você precisa colar — o resto (endpoints abaixo) a lib descobre sozinha a partir dele.",
  },
  authorization_endpoint: {
    label: "Authorization endpoint",
    purpose: "Pra onde o navegador do usuário é redirecionado pra fazer login (tela de usuário/senha).",
    whereToUse: "Campo \"Authorization URL\" / \"Authorize Endpoint\" da sua lib OIDC.",
  },
  token_endpoint: {
    label: "Token endpoint",
    purpose:
      "Troca o código de autorização (recebido depois do login) por um token de acesso — chamada feita pelo SEU BACKEND, não pelo navegador do usuário.",
    whereToUse: "Campo \"Token URL\" / \"Token Endpoint\".",
  },
  userinfo_endpoint: {
    label: "Userinfo endpoint",
    purpose: "Devolve os dados do usuário logado (nome, e-mail, etc.) a partir do token de acesso.",
    whereToUse: "Campo \"UserInfo URL\" / \"UserInfo Endpoint\".",
  },
  jwks_uri: {
    label: "JWKS URI",
    purpose: "Chaves públicas usadas pra validar a assinatura dos tokens (JWT) emitidos pelo Keycloak.",
    whereToUse: "Campo \"JWKS URI\" / \"JSON Web Key Set URL\".",
  },
  end_session_endpoint: {
    label: "End session endpoint",
    purpose: "Encerra a sessão no Keycloak — usado pra fazer logout único (single sign-out).",
    whereToUse: "Campo \"End Session Endpoint\" / \"Logout URL\".",
  },
};

function EndpointExplanation({
  field,
  value,
}: {
  field: keyof typeof ENDPOINT_INFO;
  value: string;
}) {
  const info = ENDPOINT_INFO[field];
  return (
    <div className="border border-border-subtle rounded-lg p-3 space-y-1.5">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold text-text-primary">{info.label}</p>
        <CopyButton value={value} />
      </div>
      <p className="text-xs font-mono text-text-secondary break-all">{value}</p>
      <p className="text-xs text-text-tertiary">
        <span className="font-medium text-text-secondary">Pra que serve:</span> {info.purpose}
      </p>
      <p className="text-xs text-text-tertiary">
        <span className="font-medium text-text-secondary">Onde colocar:</span> {info.whereToUse}
      </p>
    </div>
  );
}

function IssuerValidatorCard({
  issuer,
  onIssuerChange,
  onValidated,
}: {
  issuer: string;
  onIssuerChange: (v: string) => void;
  onValidated: (result: KeycloakIssuerValidationResult) => void;
}) {
  const [result, setResult] = useState<KeycloakIssuerValidationResult | null>(null);

  const mutation = useMutation({
    mutationFn: () => adminService.validateKeycloakIssuer(issuer.trim()),
    onSuccess: (r) => {
      setResult(r);
      onValidated(r);
    },
    onError: (err) => {
      setResult(null);
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao validar o issuer.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-text-primary">Validador de issuer</h2>
        <p className="text-xs text-text-tertiary mt-0.5 max-w-lg">
          Confirma o discovery document de qualquer Keycloak/realm — não precisa ser um cliente do
          PaperMoon. Útil pra checar rapidamente um Keycloak externo antes de ajudar alguém com a
          integração.
        </p>
      </div>
      <div className="flex items-end gap-3 flex-wrap">
        <div className="flex-1 min-w-[280px]">
          <label className="text-xs font-medium text-text-tertiary mb-1 block">
            Issuer (URL do realm)
          </label>
          <Input
            placeholder="https://keycloak.exemplo.com.br/realms/algum-realm"
            value={issuer}
            onChange={(e) => onIssuerChange(e.target.value)}
          />
        </div>
        <Button
          variant="secondary"
          size="sm"
          loading={mutation.isPending}
          disabled={!issuer.trim().startsWith("http")}
          onClick={() => mutation.mutate()}
        >
          Validar
        </Button>
      </div>

      {result && (
        <div className="space-y-3 pt-2 border-t border-border-subtle">
          <div
            className={cn(
              "rounded-xl border px-4 py-3 flex items-start gap-2.5",
              result.verified ? "bg-success-muted border-success/20" : "bg-warning-muted border-warning/20"
            )}
          >
            {result.verified ? (
              <CheckCircle2 size={15} className="text-success shrink-0 mt-0.5" />
            ) : (
              <XCircle size={15} className="text-warning shrink-0 mt-0.5" />
            )}
            <p className={cn("text-sm", result.verified ? "text-success" : "text-warning")}>
              {result.verified
                ? "Discovery document confirmado — o issuer é válido."
                : "Não foi possível confirmar o discovery document — endpoints abaixo são só os paths padrão do protocolo."}
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <EndpointExplanation field="issuer" value={result.issuer} />
            <EndpointExplanation field="authorization_endpoint" value={result.authorization_endpoint} />
            <EndpointExplanation field="token_endpoint" value={result.token_endpoint} />
            <EndpointExplanation field="userinfo_endpoint" value={result.userinfo_endpoint} />
            <EndpointExplanation field="jwks_uri" value={result.jwks_uri} />
            <EndpointExplanation field="end_session_endpoint" value={result.end_session_endpoint} />
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Gerador de valores pra cadastrar manualmente no admin do Keycloak ─
 * Complementa o validador acima: aquele confirma os endpoints (o que o
 * SEU sistema precisa apontar); este gera o que precisa ser DIGITADO no
 * console de admin do Keycloak pra cadastrar o client — útil quando o
 * Keycloak é de um terceiro (não temos Admin API pra criar automático).
 * Os campos espelham exatamente o payload real que
 * apps.provisioning.keycloak.KeycloakProvisioner.create_oidc_client usa
 * quando O PRÓPRIO PaperMoon cria um client automaticamente — mesma
 * configuração, só que aqui é pra alguém digitar à mão. */

const COMBINING_DIACRITICS_RE = new RegExp("[\\u0300-\\u036f]", "g");

function slugifyClientId(value: string): string {
  return value
    .normalize("NFD")
    .replace(COMBINING_DIACRITICS_RE, "") // remove acentos (combining diacritics) após NFD
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function FieldRow({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="flex items-start justify-between gap-3 py-2 border-b border-border-subtle last:border-0">
      <div className="min-w-0">
        <p className="text-xs font-semibold text-text-primary">{label}</p>
        {hint && <p className="text-xs text-text-tertiary mt-0.5">{hint}</p>}
      </div>
      <div className="flex items-center gap-1.5 shrink-0 max-w-[55%]">
        <code className="text-xs font-mono text-text-secondary break-all text-right">{value}</code>
        <CopyButton value={value} />
      </div>
    </div>
  );
}

function CodeExampleSection({
  issuer,
  clientId,
  baseUrl,
  redirectUri,
}: {
  issuer: string;
  clientId: string;
  baseUrl: string;
  redirectUri: string;
}) {
  const [language, setLanguage] = useState<KeycloakIntegrationLanguage>("nextjs");
  const [result, setResult] = useState<KeycloakCodeSnippetResult | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      adminService.renderKeycloakCodeSnippet({
        language,
        issuer,
        client_id: clientId,
        base_url: baseUrl,
        redirect_uri: redirectUri,
      }),
    onSuccess: setResult,
    onError: (err) => {
      setResult(null);
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao gerar o exemplo de código.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const canGenerate = issuer.trim().startsWith("http");

  return (
    <div className="space-y-4 pt-3 border-t border-border-subtle">
      <div>
        <Badge variant="info">4. Exemplo de código</Badge>
        <p className="text-xs text-text-tertiary mt-1.5 max-w-lg">
          Escolha a linguagem/framework do sistema do cliente — gera um exemplo pronto (função ou
          classe de configuração OIDC) usando os valores acima e o issuer validado no card de cima.
        </p>
      </div>

      {!canGenerate && (
        <p className="text-xs text-warning">
          Valide um issuer no card &quot;Validador de issuer&quot; acima primeiro.
        </p>
      )}

      <LanguageTabs value={language} onChange={setLanguage} />

      <Button
        variant="secondary"
        size="sm"
        loading={mutation.isPending}
        disabled={!canGenerate}
        onClick={() => mutation.mutate()}
      >
        Gerar exemplo
      </Button>

      {result && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="text-sm font-semibold text-text-primary">
              Código ({result.package})
              {result.public_client && (
                <span className="ml-2 text-xs font-normal text-text-tertiary">
                  client público — sem client_secret de verdade
                </span>
              )}
            </h3>
            <code className="bg-surface-3 px-1.5 py-0.5 rounded font-mono text-xs text-info">
              {result.install_command}
            </code>
          </div>
          <ol className="space-y-2">
            {result.steps.map((step, i) => (
              <li key={i} className="flex gap-3 text-sm text-text-secondary">
                <span className="shrink-0 w-5 h-5 rounded-full bg-surface-3 text-text-tertiary text-xs font-semibold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
          <CodeBlock code={result.code_snippet} />
        </div>
      )}
    </div>
  );
}

function ManualClientSetupCard({ issuer }: { issuer: string }) {
  const [appName, setAppName] = useState("");
  const [redirectUri, setRedirectUri] = useState("");
  const [clientType, setClientType] = useState<"confidential" | "public">("confidential");
  const nameId = useId();
  const redirectId = useId();

  let rootUrl = "";
  try {
    rootUrl = redirectUri ? new URL(redirectUri).origin : "";
  } catch {
    rootUrl = "";
  }

  const clientId = slugifyClientId(appName) || "minha-aplicacao";
  const canGenerate = Boolean(appName.trim()) && rootUrl !== "";

  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-text-primary">
          O que preencher no admin do Keycloak
        </h2>
        <p className="text-xs text-text-tertiary mt-0.5 max-w-lg">
          Coloque a URL de callback do sistema do cliente e o tipo de client — a página gera os
          valores exatos pra digitar em <strong>Clients → Create client</strong> no console de
          admin do Keycloak, campo a campo.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label htmlFor={nameId} className="text-xs font-medium text-text-tertiary mb-1 block">
            Nome do sistema do cliente
          </label>
          <Input
            id={nameId}
            placeholder="Ex: Portal do Fornecedor"
            value={appName}
            onChange={(e) => setAppName(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor={redirectId} className="text-xs font-medium text-text-tertiary mb-1 block">
            URL de callback (redirect URI) do sistema
          </label>
          <Input
            id={redirectId}
            placeholder="https://sistemadocliente.com.br/auth/callback"
            value={redirectUri}
            onChange={(e) => setRedirectUri(e.target.value)}
          />
        </div>
      </div>

      <div>
        <span className="text-xs font-medium text-text-tertiary mb-1.5 block">Tipo de client</span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setClientType("confidential")}
            className={cn(
              "px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors",
              clientType === "confidential"
                ? "bg-brand-accent/12 border-brand-accent/30 text-brand-accent"
                : "border-border-subtle text-text-tertiary hover:text-text-secondary"
            )}
          >
            Confidencial (tem backend, guarda secret)
          </button>
          <button
            type="button"
            onClick={() => setClientType("public")}
            className={cn(
              "px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors",
              clientType === "public"
                ? "bg-brand-accent/12 border-brand-accent/30 text-brand-accent"
                : "border-border-subtle text-text-tertiary hover:text-text-secondary"
            )}
          >
            Público (SPA, sem onde guardar secret)
          </button>
        </div>
      </div>

      {canGenerate && (
        <div className="space-y-5 pt-3 border-t border-border-subtle">
          <div>
            <Badge variant="info">1. General settings</Badge>
            <div className="mt-2">
              <FieldRow
                label="Client type"
                value="OpenID Connect"
                hint="Primeiro campo do wizard, já vem assim por padrão."
              />
              <FieldRow
                label="Client ID"
                value={clientId}
                hint="Identificador único do client dentro do realm — o cliente vai usar isso na config OIDC do sistema dele."
              />
            </div>
          </div>

          <div>
            <Badge variant="info">2. Capability config</Badge>
            <div className="mt-2">
              <FieldRow
                label="Client authentication"
                value={clientType === "confidential" ? "On" : "Off"}
                hint={
                  clientType === "confidential"
                    ? "Liga porque o sistema tem um backend capaz de guardar o client secret com segurança."
                    : "Desliga porque é um app 100% front-end (SPA) — não existe onde guardar um secret em segredo."
                }
              />
              <FieldRow
                label="Authorization"
                value="Off"
                hint="Fine-grained permissions do Keycloak — não é necessário pro fluxo de login padrão."
              />
              <FieldRow
                label="Authentication flow — Standard flow"
                value="On"
                hint="Authorization Code flow — o fluxo de login padrão, com PKCE quando o client é público."
              />
              <FieldRow
                label="Authentication flow — Direct access grants"
                value="Off"
                hint="Desliga: não deixa trocar usuário/senha diretamente por um token sem passar pela tela de login."
              />
              <FieldRow
                label="Authentication flow — Implicit flow"
                value="Off"
                hint="Fluxo antigo e inseguro — sempre desligado."
              />
              <FieldRow
                label="Authentication flow — Service accounts roles"
                value="Off"
                hint="Só liga se esse sistema também precisar chamar outras APIs em nome dele mesmo (client credentials) — não é o caso do login normal."
              />
            </div>
          </div>

          <div>
            <Badge variant="info">3. Login settings</Badge>
            <div className="mt-2">
              <FieldRow label="Root URL" value={rootUrl} hint="A origem (protocolo + domínio) do sistema." />
              <FieldRow label="Home URL" value={rootUrl} hint="Pra onde o Keycloak manda o usuário se não houver redirect_uri explícito." />
              <FieldRow
                label="Valid redirect URIs"
                value={redirectUri}
                hint="A URL exata de callback informada acima — o Keycloak só aceita redirecionar pra URLs cadastradas aqui."
              />
              <FieldRow
                label="Valid post logout redirect URIs"
                value={`${rootUrl}/*`}
                hint="Pra onde o usuário pode ser mandado depois do logout."
              />
              <FieldRow
                label="Web origins"
                value={clientType === "public" ? rootUrl : "(deixe em branco)"}
                hint={
                  clientType === "public"
                    ? "Necessário pro navegador poder chamar o Keycloak via CORS direto do front-end."
                    : "Não precisa — a troca de código por token acontece no backend, não no navegador."
                }
              />
            </div>
          </div>

          <CodeExampleSection
            issuer={issuer}
            clientId={clientId}
            baseUrl={rootUrl}
            redirectUri={redirectUri}
          />
        </div>
      )}
    </div>
  );
}

/* ── Seletor de cliente ────────────────────────────────────────────── */

function CustomerPicker({
  customerId,
  onSelect,
}: {
  customerId: string;
  onSelect: (id: string) => void;
}) {
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-customers-keycloak-picker", search],
    queryFn: () => adminService.listCustomers({ search: search || undefined, page: 1 }),
    staleTime: 30_000,
  });

  const customers = data?.results ?? [];

  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-text-primary">Criar/gerenciar integração de um cliente</h2>
        <p className="text-xs text-text-tertiary mt-0.5">
          Escolha o cliente pra ver, gerar o guia ou criar uma integração real em nome dele —
          mesma funcionalidade da página do cliente, como ferramenta de suporte.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label
            htmlFor="kc_customer_search"
            className="text-xs font-medium text-text-tertiary mb-1 block"
          >
            Buscar cliente
          </label>
          <Input
            id="kc_customer_search"
            placeholder="Nome da empresa…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            leftElement={<Search size={14} />}
          />
        </div>
        <div>
          <label
            htmlFor="kc_customer_select"
            className="text-xs font-medium text-text-tertiary mb-1 block"
          >
            Cliente
          </label>
          <select
            id="kc_customer_select"
            value={customerId}
            onChange={(e) => onSelect(e.target.value)}
            disabled={isLoading}
            className="w-full rounded-md border border-border-default bg-surface-2 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-border-focus disabled:opacity-50"
          >
            <option value="">Selecionar cliente…</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.company_name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

/* ── Página ────────────────────────────────────────────────────────── */

export default function BackofficeKeycloakIntegrationsPage() {
  const [customerId, setCustomerId] = useState("");
  const [issuer, setIssuer] = useState("");

  return (
    <div className="space-y-8">
      <PageHeader
        title="Integração Keycloak"
        description="Ferramentas de suporte: valide um issuer qualquer, ou crie/veja integrações em nome de um cliente"
      />

      <IssuerValidatorCard
        issuer={issuer}
        onIssuerChange={setIssuer}
        onValidated={(result) => setIssuer(result.issuer)}
      />
      <ManualClientSetupCard issuer={issuer} />
      <CustomerPicker customerId={customerId} onSelect={setCustomerId} />

      {customerId && (
        <KeycloakIntegrationManager
          key={customerId}
          queryKeyPrefix={["admin-keycloak-integrations", customerId]}
          services={{
            listIntegrations: () => adminService.listCustomerKeycloakIntegrations(customerId),
            createIntegration: (payload) =>
              adminService.createCustomerKeycloakIntegration(customerId, payload),
            getGuide: (params) => adminService.getCustomerKeycloakGuide(customerId, params),
            getSecret: (integrationId) =>
              adminService.getCustomerKeycloakIntegrationSecret(customerId, integrationId),
          }}
          getUnavailableCopy={(reason) => ({
            title: "Integração Keycloak não está disponível pra esse cliente",
            description:
              reason === "platform_not_configured"
                ? "A conexão central do PaperMoon com o Keycloak não está configurada/ativa — configure em Configurações → Conexão com o Keycloak antes de continuar."
                : "Esse cliente não tem um serviço 'keycloak' ativo (realm provisionado) — verifique a assinatura/provisionamento dele.",
            action:
              reason === "platform_not_configured"
                ? { label: "Ir pra Configurações", href: "/backoffice/settings" }
                : undefined,
          })}
        />
      )}

      {!customerId && (
        <div className="flex items-center gap-2 text-xs text-text-tertiary">
          <Badge variant="muted">Nenhum cliente selecionado</Badge>
          Escolha um cliente acima pra ver ou criar integrações.
        </div>
      )}
    </div>
  );
}
