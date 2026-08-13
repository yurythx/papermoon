"use client";

import axios from "axios";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/compound/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { cardClass } from "@/components/ui/card";
import { Toggle } from "@/components/ui/toggle";
import { cn } from "@/lib/utils";
import { KeyRound, Copy, CheckCircle2, XCircle, Network } from "lucide-react";
import type { KeycloakConnectionConfig, SSOConfig } from "@/types";

function TestResultBanner({ result }: { result: { reachable: boolean; message: string } | null }) {
  if (!result) return null;
  return (
    <div
      className={cn(
        "rounded-xl border px-4 py-3 flex items-start gap-2.5",
        result.reachable ? "bg-success-muted border-success/20" : "bg-danger-muted border-danger/20"
      )}
    >
      {result.reachable ? (
        <CheckCircle2 size={15} className="text-success shrink-0 mt-0.5" />
      ) : (
        <XCircle size={15} className="text-danger shrink-0 mt-0.5" />
      )}
      <p className={cn("text-sm", result.reachable ? "text-success" : "text-danger")}>{result.message}</p>
    </div>
  );
}

/* ── Card: SSO de staff ────────────────────────────────────────────── */

function SsoConfigCard() {
  const queryClient = useQueryClient();

  const { data: config, isLoading } = useQuery({
    queryKey: ["sso-config"],
    queryFn: adminService.getSSOConfig,
  });

  const [enabled, setEnabled] = useState(false);
  const [issuer, setIssuer] = useState("");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [staffGroup, setStaffGroup] = useState("");
  const [testResult, setTestResult] = useState<{ reachable: boolean; message: string } | null>(null);

  useEffect(() => {
    if (!config) return;
    setEnabled(config.enabled);
    setIssuer(config.issuer);
    setClientId(config.client_id);
    setClientSecret("");
    setStaffGroup(config.staff_group);
  }, [config]);

  const saveMutation = useMutation({
    mutationFn: () =>
      adminService.updateSSOConfig({
        enabled,
        issuer,
        client_id: clientId,
        client_secret: clientSecret || undefined,
        staff_group: staffGroup,
      }),
    onSuccess: (updated: SSOConfig) => {
      queryClient.setQueryData(["sso-config"], updated);
      setClientSecret("");
      setTestResult(null);
      toast.success(updated.enabled ? "SSO ativado e salvo." : "Configuração salva. SSO desativado.");
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao salvar configuração.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const testMutation = useMutation({
    mutationFn: () => adminService.testSSOConfig(issuer || undefined),
    onSuccess: (result) => setTestResult(result),
    onError: (err) => {
      setTestResult(null);
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao testar conexão.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  function copyRedirectUri() {
    if (!config) return;
    navigator.clipboard.writeText(config.redirect_uri);
    toast.success("Redirect URI copiado.");
  }

  if (isLoading) {
    return <Skeleton className="h-64 w-full rounded-xl" />;
  }

  const canActivate = Boolean(issuer && clientId && (clientSecret || config?.client_secret_set));

  return (
    <div className={cardClass({ className: "p-6 space-y-5" })}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface-2 border border-border-subtle">
            <KeyRound size={16} className="text-brand-accent" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Login via Keycloak (SSO)</h2>
            <p className="text-xs text-text-tertiary mt-0.5 max-w-md">
              Quando ativado, a tela de login (<code className="text-[11px]">/login</code>) passa a
              mostrar o botão &quot;Entrar com Keycloak&quot; para contas de staff. O login por e-mail e
              senha continua funcionando normalmente — SSO é um método adicional, não substitui o padrão.
            </p>
          </div>
        </div>
        <Toggle checked={enabled} onChange={setEnabled} disabled={saveMutation.isPending} />
      </div>

      <div className="space-y-4 pt-4 border-t border-border-subtle">
        <div className="space-y-1">
          <label htmlFor="sso_issuer" className="block text-sm font-medium text-text-secondary">
            Issuer (URL do realm)
          </label>
          <Input
            id="sso_issuer"
            type="text"
            value={issuer}
            onChange={(e) => setIssuer(e.target.value)}
            placeholder="https://keycloak.suaempresa.com/realms/papermoon-staff"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="sso_client_id" className="block text-sm font-medium text-text-secondary">
            Client ID
          </label>
          <Input
            id="sso_client_id"
            type="text"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            placeholder="papermoon-backoffice"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="sso_client_secret" className="block text-sm font-medium text-text-secondary">
            Client Secret
          </label>
          <PasswordInput
            id="sso_client_secret"
            value={clientSecret}
            onChange={(e) => setClientSecret(e.target.value)}
            placeholder={config?.client_secret_set ? "•••••••• (deixe em branco para manter)" : "Cole o client secret do Keycloak"}
            autoComplete="off"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="sso_staff_group" className="block text-sm font-medium text-text-secondary">
            Staff group
            <span className="ml-1.5 text-xs font-normal text-text-tertiary">(opcional)</span>
          </label>
          <Input
            id="sso_staff_group"
            type="text"
            value={staffGroup}
            onChange={(e) => setStaffGroup(e.target.value)}
            placeholder="papermoon-staff"
          />
          <p className="text-xs text-text-tertiary mt-1 max-w-md">
            Nome do grupo do Keycloak (claim <code className="text-[11px]">groups</code> do id_token)
            que autoriza criar uma conta staff automaticamente no primeiro login de um e-mail novo
            (JIT provisioning). Em branco: só e-mails já cadastrados como staff conseguem entrar via
            SSO — nenhuma conta é criada sozinha.
          </p>
        </div>

        <div className="space-y-1">
          <label htmlFor="sso_redirect_uri" className="block text-sm font-medium text-text-secondary">
            Redirect URI
            <span className="ml-1.5 text-xs font-normal text-text-tertiary">
              (cole exatamente isso no client do Keycloak)
            </span>
          </label>
          <Input
            id="sso_redirect_uri"
            type="text"
            value={config?.redirect_uri ?? ""}
            readOnly
            className="opacity-70 cursor-not-allowed font-mono text-xs"
            rightElement={
              <button
                type="button"
                onClick={copyRedirectUri}
                aria-label="Copiar redirect URI"
                className="rounded-sm text-text-tertiary hover:text-text-secondary transition-colors cursor-pointer"
              >
                <Copy size={14} />
              </button>
            }
          />
        </div>
      </div>

      <TestResultBanner result={testResult} />

      <div className="flex items-center gap-3 pt-1">
        <Button
          variant="primary"
          size="sm"
          loading={saveMutation.isPending}
          disabled={enabled && !canActivate}
          onClick={() => saveMutation.mutate()}
        >
          Salvar
        </Button>
        <Button
          variant="secondary"
          size="sm"
          loading={testMutation.isPending}
          disabled={!issuer}
          onClick={() => testMutation.mutate()}
        >
          Testar conexão
        </Button>
      </div>

      {config?.updated_at && (
        <p className="text-xs text-text-tertiary">
          Última atualização {config.updated_by_email ? `por ${config.updated_by_email} ` : ""}
          em {new Date(config.updated_at).toLocaleString("pt-BR")}
        </p>
      )}
    </div>
  );
}

/* ── Card: conexão central com o Keycloak (provisionamento) ──────────── */

function KeycloakConnectionCard() {
  const queryClient = useQueryClient();

  const { data: config, isLoading } = useQuery({
    queryKey: ["keycloak-connection"],
    queryFn: adminService.getKeycloakConnection,
  });

  const [enabled, setEnabled] = useState(false);
  const [apiUrl, setApiUrl] = useState("");
  const [adminToken, setAdminToken] = useState("");
  const [testResult, setTestResult] = useState<{ reachable: boolean; message: string } | null>(null);

  useEffect(() => {
    if (!config) return;
    setEnabled(config.enabled);
    setApiUrl(config.api_url);
    setAdminToken("");
  }, [config]);

  const saveMutation = useMutation({
    mutationFn: () =>
      adminService.updateKeycloakConnection({
        enabled,
        api_url: apiUrl,
        admin_token: adminToken || undefined,
      }),
    onSuccess: (updated: KeycloakConnectionConfig) => {
      queryClient.setQueryData(["keycloak-connection"], updated);
      setAdminToken("");
      setTestResult(null);
      toast.success(
        updated.enabled
          ? "Conexão ativada e salva. Integrações com outros sistemas já estão disponíveis pros clientes."
          : "Configuração salva. Conexão desativada."
      );
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao salvar conexão.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const testMutation = useMutation({
    mutationFn: () => adminService.testKeycloakConnection(apiUrl || undefined, adminToken || undefined),
    onSuccess: (result) => setTestResult(result),
    onError: (err) => {
      setTestResult(null);
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao testar conexão.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  if (isLoading) {
    return <Skeleton className="h-64 w-full rounded-xl" />;
  }

  const canActivate = Boolean(apiUrl && (adminToken || config?.admin_token_set));

  return (
    <div className={cardClass({ className: "p-6 space-y-5" })}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface-2 border border-border-subtle">
            <Network size={16} className="text-brand-accent" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-text-primary">
              Conexão com o Keycloak (provisionamento)
            </h2>
            <p className="text-xs text-text-tertiary mt-0.5 max-w-md">
              Não é o login de staff acima — esta é a conexão que o PaperMoon usa pra administrar
              realms e clients de CLIENTES via Admin REST API. Precisa estar ativa e testada com
              sucesso antes que a página &quot;Integração SSO&quot; do dashboard do cliente fique
              disponível.
            </p>
          </div>
        </div>
        <Toggle checked={enabled} onChange={setEnabled} disabled={saveMutation.isPending} />
      </div>

      <div className="space-y-4 pt-4 border-t border-border-subtle">
        <div className="space-y-1">
          <label htmlFor="kc_api_url" className="block text-sm font-medium text-text-secondary">
            URL da API (base do Keycloak)
          </label>
          <Input
            id="kc_api_url"
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="https://auth.papermoon.com"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="kc_admin_token" className="block text-sm font-medium text-text-secondary">
            Admin token
          </label>
          <PasswordInput
            id="kc_admin_token"
            value={adminToken}
            onChange={(e) => setAdminToken(e.target.value)}
            placeholder={config?.admin_token_set ? "•••••••• (deixe em branco para manter)" : "Cole o token de admin do Keycloak"}
            autoComplete="off"
          />
          <p className="text-xs text-text-tertiary mt-1 max-w-md">
            Token de um service account (ou sessão de admin) com permissão pra criar/editar realms
            e clients via <code className="text-[11px]">/admin/realms/...</code>.
          </p>
        </div>
      </div>

      <TestResultBanner result={testResult} />

      <div className="flex items-center gap-3 pt-1">
        <Button
          variant="primary"
          size="sm"
          loading={saveMutation.isPending}
          disabled={enabled && !canActivate}
          onClick={() => saveMutation.mutate()}
        >
          Salvar
        </Button>
        <Button
          variant="secondary"
          size="sm"
          loading={testMutation.isPending}
          disabled={!apiUrl && !config?.api_url}
          onClick={() => testMutation.mutate()}
        >
          Testar conexão
        </Button>
      </div>

      {config?.updated_at && (
        <p className="text-xs text-text-tertiary">
          Última atualização {config.updated_by_email ? `por ${config.updated_by_email} ` : ""}
          em {new Date(config.updated_at).toLocaleString("pt-BR")}
        </p>
      )}
    </div>
  );
}

/* ── Page ───────────────────────────────────────────────────────────── */

export default function BackofficeSettingsPage() {
  return (
    <div className="space-y-8 max-w-2xl">
      <PageHeader title="Configurações" description="SSO e integrações do backoffice" />
      <SsoConfigCard />
      <KeycloakConnectionCard />
    </div>
  );
}
