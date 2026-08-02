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
import { cn } from "@/lib/utils";
import { KeyRound, Copy, CheckCircle2, XCircle } from "lucide-react";
import type { SSOConfig } from "@/types";

/* ── Toggle ─────────────────────────────────────────────────────────── */

function Toggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-1",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        checked ? "bg-brand-accent" : "bg-surface-3 border border-border-default"
      )}
    >
      <span
        className={cn(
          "inline-block h-4 w-4 transform rounded-full bg-[rgb(var(--papermoon-moonlight-fixed-rgb))] transition-transform duration-150",
          checked ? "translate-x-6" : "translate-x-1"
        )}
      />
    </button>
  );
}

/* ── Page ───────────────────────────────────────────────────────────── */

export default function BackofficeSettingsPage() {
  const queryClient = useQueryClient();

  const { data: config, isLoading } = useQuery({
    queryKey: ["sso-config"],
    queryFn: adminService.getSSOConfig,
  });

  const [enabled, setEnabled] = useState(false);
  const [issuer, setIssuer] = useState("");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [testResult, setTestResult] = useState<{ reachable: boolean; message: string } | null>(null);

  useEffect(() => {
    if (!config) return;
    setEnabled(config.enabled);
    setIssuer(config.issuer);
    setClientId(config.client_id);
    setClientSecret("");
  }, [config]);

  const saveMutation = useMutation({
    mutationFn: () =>
      adminService.updateSSOConfig({
        enabled,
        issuer,
        client_id: clientId,
        client_secret: clientSecret || undefined,
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
    return (
      <div className="max-w-2xl space-y-8">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  const canActivate = Boolean(issuer && clientId && (clientSecret || config?.client_secret_set));

  return (
    <div className="space-y-8 max-w-2xl">
      <PageHeader title="Configurações" description="SSO e integrações do backoffice" />

      <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-5">
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

        {testResult && (
          <div
            className={cn(
              "rounded-xl border px-4 py-3 flex items-start gap-2.5",
              testResult.reachable
                ? "bg-success-muted border-success/20"
                : "bg-danger-muted border-danger/20"
            )}
          >
            {testResult.reachable ? (
              <CheckCircle2 size={15} className="text-success shrink-0 mt-0.5" />
            ) : (
              <XCircle size={15} className="text-danger shrink-0 mt-0.5" />
            )}
            <p className={cn("text-sm", testResult.reachable ? "text-success" : "text-danger")}>
              {testResult.message}
            </p>
          </div>
        )}

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
    </div>
  );
}
