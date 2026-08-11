"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";
import { CheckCircle2, Search, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/compound/page-header";
import { KeycloakIntegrationManager } from "@/components/keycloak/keycloak-integration-manager";
import { adminService } from "@/lib/services";
import { cn } from "@/lib/utils";
import type { KeycloakIssuerValidationResult } from "@/types";

/* ── Validador genérico de issuer, sem vínculo com cliente nenhum ────── */

function IssuerValidatorCard() {
  const [issuer, setIssuer] = useState("");
  const [result, setResult] = useState<KeycloakIssuerValidationResult | null>(null);

  const mutation = useMutation({
    mutationFn: () => adminService.validateKeycloakIssuer(issuer.trim()),
    onSuccess: setResult,
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
            onChange={(e) => setIssuer(e.target.value)}
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
          <dl className="grid gap-2 text-xs font-mono">
            {(
              [
                ["authorization_endpoint", result.authorization_endpoint],
                ["token_endpoint", result.token_endpoint],
                ["userinfo_endpoint", result.userinfo_endpoint],
                ["jwks_uri", result.jwks_uri],
                ["end_session_endpoint", result.end_session_endpoint],
              ] as const
            ).map(([label, value]) => (
              <div key={label} className="flex gap-2">
                <dt className="text-text-tertiary shrink-0">{label}:</dt>
                <dd className="text-text-secondary break-all">{value}</dd>
              </div>
            ))}
          </dl>
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

  return (
    <div className="space-y-8">
      <PageHeader
        title="Integração Keycloak"
        description="Ferramentas de suporte: valide um issuer qualquer, ou crie/veja integrações em nome de um cliente"
      />

      <IssuerValidatorCard />
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
