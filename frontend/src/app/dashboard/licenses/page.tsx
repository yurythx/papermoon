"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { licenseService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/compound/status-badge";
import { TimeProgress } from "@/components/compound/time-progress";
import { EmptyState } from "@/components/compound/empty-state";
import { PageHeader } from "@/components/compound/page-header";
import { Badge } from "@/components/ui/badge";
import { Key, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import type { License } from "@/types";

const SERVICE_LABEL: Record<string, string> = {
  n8n: "n8n",
  chatwoot: "Chatwoot",
  meta_whatsapp: "WhatsApp API",
  glpi: "GLPI Helpdesk",
  zabbix: "Zabbix",
  proxmox: "Proxmox VE",
  nextcloud: "Nextcloud",
  aapanel: "AAPanel",
  evolution_api: "Evolution API",
  tailscale: "Tailscale",
};

type CardState =
  | "healthy"
  | "expiring-soon"
  | "expiring-urgent"
  | "critical"
  | "suspended"
  | "expired";

function getCardState(license: License): CardState {
  if (license.status === "suspended") return "suspended";
  if (license.status === "expired") return "expired";
  if (license.days_remaining <= 3) return "critical";
  if (license.days_remaining <= 7) return "expiring-urgent";
  if (license.days_remaining <= 15) return "expiring-soon";
  return "healthy";
}

const cardBorderMap: Record<CardState, string> = {
  healthy:          "border-border-subtle hover:border-border-focus",
  "expiring-soon":  "border-warning/20 hover:border-warning/40",
  "expiring-urgent":"border-warning/40 hover:border-warning/60",
  critical:         "border-danger/40 hover:border-danger/60",
  suspended:        "border-danger/30 hover:border-danger/50",
  expired:          "border-border-subtle opacity-70 hover:border-border-default",
};

export default function LicensesPage() {
  const { data: licenses, isLoading } = useQuery({
    queryKey: ["licenses"],
    queryFn: licenseService.list,
  });

  const results = licenses?.results ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Minhas Licenças"
        description="Produtos contratados e status de acesso"
      />

      {isLoading ? (
        <LicensesPageSkeleton />
      ) : results.length === 0 ? (
        <EmptyState
          title="Nenhuma licença ativa"
          description="Explore o catálogo e ative seu primeiro produto para ver as licenças aqui."
          icon={Key}
          action={{ label: "Explorar Catálogo", href: "/dashboard/catalog" }}
        />
      ) : (
        <div className="space-y-4">
          {results.map((license) => (
            <Link
              key={license.id}
              href={`/dashboard/licenses/${license.id}`}
              className="block group"
            >
              <LicenseCard license={license} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function LicenseCard({ license }: { license: License }) {
  const state = getCardState(license);

  return (
    <div
      className={cn(
        "bg-surface-1 border rounded-xl p-5 transition-all duration-150 space-y-4",
        cardBorderMap[state]
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-base font-semibold text-text-primary group-hover:text-white transition-colors truncate">
              {license.product_name}
            </h2>
            <StatusBadge status={license.status} />
          </div>
          <p className="text-xs text-text-tertiary font-mono">{license.key}</p>
        </div>

        <div className="shrink-0 text-right">
          <p className="text-sm font-semibold text-text-primary tabular-nums">
            R$ {parseFloat(license.amount).toFixed(2)}
          </p>
          <p className="text-xs text-text-tertiary">
            {license.billing_cycle === "monthly"
              ? "por mês"
              : license.billing_cycle === "annual"
              ? "por ano"
              : "cobrança única"}
          </p>
        </div>
      </div>

      {/* Temporal progress */}
      {license.status !== "expired" && (
        <TimeProgress
          startDate={license.created_at}
          endDate={license.valid_until}
        />
      )}
      {license.status === "expired" && (
        <p className="text-xs text-danger">
          Expirou em {new Date(license.valid_until).toLocaleDateString("pt-BR")}
        </p>
      )}

      {/* Services row */}
      {license.services.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border-subtle">
          <Zap size={12} className="text-text-tertiary" />
          {license.services.map((sa) => (
            <Badge
              key={sa.id}
              variant={
                sa.status === "active"       ? "success"
                : sa.status === "provisioning" ? "info"
                : sa.status === "failed"       ? "danger"
                : "muted"
              }
              dot
            >
              {SERVICE_LABEL[sa.service_key] ?? sa.service_key}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function LicensesPageSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-surface-1 border border-border-subtle rounded-xl p-5 space-y-4">
          <div className="flex justify-between">
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-10 w-20" />
          </div>
          <Skeleton className="h-1.5 w-full" />
          <div className="flex gap-2">
            <Skeleton className="h-5 w-16 rounded-md" />
            <Skeleton className="h-5 w-20 rounded-md" />
          </div>
        </div>
      ))}
    </div>
  );
}
