"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { subscriptionService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/compound/status-badge";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { Package, ExternalLink, CheckCircle2, AlertCircle, Clock, Info, Mail } from "lucide-react";
import type { ServiceAccess, Subscription } from "@/types";

const SERVICE_LABELS: Record<string, string> = {
  chatwoot: "Chatwoot",
  n8n: "n8n",
  meta_whatsapp: "WhatsApp Meta",
  evolution_api: "Evolution API",
  glpi: "GLPI Helpdesk",
  zabbix: "Zabbix",
  proxmox: "Proxmox VE",
  truenas: "TrueNAS",
  nextcloud: "Nextcloud",
  aapanel: "AAPanel",
  tailscale: "Tailscale",
};

const CYCLE_LABEL: Record<string, string> = {
  monthly: "Mensal",
  annual: "Anual",
  one_time: "Cobrança única",
  lifetime: "Vitalício",
};

export default function SubscriptionsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: subscriptionService.list,
  });

  const subscriptions = Array.isArray(data) ? data : (data?.results ?? []);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Meus Contratos"
        description="Serviços contratados e acessos provisionados"
      />

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-surface-1 border border-border-subtle rounded-xl p-5 space-y-3">
              <div className="flex justify-between">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-5 w-16" />
              </div>
              <div className="grid grid-cols-3 gap-4">
                {[1, 2, 3].map((j) => <Skeleton key={j} className="h-3 w-full" />)}
              </div>
            </div>
          ))}
        </div>
      ) : subscriptions.length === 0 ? (
        <EmptyState
          title="Nenhum contrato encontrado"
          icon={Package}
          description="Você ainda não tem contratos ativos. Explore o catálogo para descobrir os serviços disponíveis para a sua operação."
          action={{ label: "Ver catálogo", href: "/dashboard/catalog", variant: "primary" }}
        />
      ) : (
        <div className="space-y-4">
          {subscriptions.map((sub) => (
            <SubscriptionCard key={sub.id} subscription={sub} />
          ))}
        </div>
      )}

      {/* Support footer */}
      <div className="flex items-center gap-3 rounded-xl border border-border-subtle bg-surface-1 px-5 py-4">
        <Mail size={14} className="text-text-tertiary shrink-0" />
        <p className="text-xs text-text-secondary flex-1">
          Precisa solicitar alterações, cancelamentos ou novos serviços?{" "}
          <a href="mailto:contato@papermoon.com.br" className="text-brand-accent hover:underline font-medium">
            Fale com nossa equipe
          </a>
          .
        </p>
      </div>
    </div>
  );
}

function ServiceAccessRow({ sa }: { sa: ServiceAccess }) {
  const label = SERVICE_LABELS[sa.service_key] ?? sa.service_key;

  const statusIcon = {
    active: <CheckCircle2 size={13} className="text-success shrink-0" />,
    provisioning: <Clock size={13} className="text-warning shrink-0" />,
    suspended: <AlertCircle size={13} className="text-danger shrink-0" />,
    failed: <AlertCircle size={13} className="text-danger shrink-0" />,
  }[sa.status] ?? <Info size={13} className="text-text-tertiary shrink-0" />;

  const statusLabel = {
    active: "Ativo",
    provisioning: "Provisionando…",
    suspended: "Suspenso",
    failed: "Falha",
  }[sa.status] ?? sa.status;

  return (
    <div className="flex items-center justify-between py-2 border-b border-border-subtle last:border-0">
      <div className="flex items-center gap-2">
        {statusIcon}
        <span className="text-sm text-text-primary font-medium">{label}</span>
        <span className="text-xs text-text-tertiary">— {statusLabel}</span>
        {sa.service_key === "meta_whatsapp" && sa.external_id && (
          <Badge variant="info" className="text-xs">{sa.external_id}</Badge>
        )}
        {sa.error && (
          <span className="text-xs text-danger truncate max-w-xs" title={sa.error}>
            {sa.error}
          </span>
        )}
      </div>
      {sa.service_url && sa.status === "active" && (
        <a
          href={sa.service_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-brand-accent hover:underline shrink-0"
        >
          Acessar <ExternalLink size={11} />
        </a>
      )}
    </div>
  );
}

function SubscriptionCard({ subscription: sub }: { subscription: Subscription }) {
  const startsAt = new Date(sub.starts_at).toLocaleDateString("pt-BR");
  const expiresAt = new Date(sub.expires_at).toLocaleDateString("pt-BR");
  const serviceAccesses = sub.license?.service_accesses ?? [];

  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl p-5">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="font-semibold text-text-primary">{sub.product_name}</p>
          <p className="text-xs text-text-tertiary font-mono mt-0.5">{sub.id}</p>
        </div>
        <StatusBadge status={sub.status} />
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <p className="text-xs text-text-tertiary mb-1">Ciclo</p>
          <p className="text-sm text-text-secondary">
            {CYCLE_LABEL[sub.billing_cycle] ?? sub.billing_cycle}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-tertiary mb-1">Valor</p>
          <p className="text-sm text-text-secondary tabular-nums">
            R$ {parseFloat(sub.amount).toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-tertiary mb-1">Vigência</p>
          <p className="text-sm text-text-secondary">{startsAt} – {expiresAt}</p>
        </div>
      </div>

      {/* Service accesses */}
      {serviceAccesses.length > 0 && (
        <div className="border-t border-border-subtle pt-4">
          <p className="text-xs font-semibold text-text-tertiary uppercase tracking-wide mb-2">
            Serviços incluídos
          </p>
          <div>
            {serviceAccesses.map((sa) => (
              <ServiceAccessRow key={sa.id} sa={sa} />
            ))}
          </div>
        </div>
      )}

      {/* Fallback link when no service accesses */}
      {sub.license && serviceAccesses.length === 0 && (
        <div className="mt-4 pt-4 border-t border-border-subtle flex items-center justify-between">
          <p className="text-xs text-text-tertiary">Licença ativa</p>
          <Link href={`/dashboard/licenses/${sub.license.id}`} className="text-xs text-brand-accent hover:underline">
            Ver detalhes →
          </Link>
        </div>
      )}
    </div>
  );
}
