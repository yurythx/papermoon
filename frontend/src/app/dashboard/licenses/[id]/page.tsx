"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { licenseService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/compound/status-badge";
import { TimeProgress } from "@/components/compound/time-progress";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, Copy } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import type { ServiceAccess } from "@/types";

export default function LicenseDetailPage({ params }: { params: { id: string } }) {
  const { data: license, isLoading, isError } = useQuery({
    queryKey: ["license", params.id],
    queryFn: () => licenseService.get(params.id),
  });

  if (isLoading) return <DetailSkeleton />;

  if (isError || !license) {
    return (
      <div className="text-center py-20">
        <p className="text-sm text-text-secondary">Licença não encontrada.</p>
        <Link href="/dashboard/licenses" className="text-xs text-brand-accent underline mt-2 block">
          Voltar para licenças
        </Link>
      </div>
    );
  }

  const validFrom = new Date(license.valid_from).toLocaleDateString("pt-BR");
  const validUntil = new Date(license.valid_until).toLocaleDateString("pt-BR");

  function copyKey() {
    navigator.clipboard.writeText(license!.key);
    toast.success("Chave copiada!");
  }

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Breadcrumb */}
      <Link
        href="/dashboard/licenses"
        className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
        <ChevronLeft size={14} />
        Minhas Licenças
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">
            {license.product_name}
          </h1>
          <button
            onClick={copyKey}
            className="flex items-center gap-1.5 mt-2 group"
            title="Copiar chave"
          >
            <p className="text-xs text-text-tertiary font-mono group-hover:text-text-secondary transition-colors">
              {license.key}
            </p>
            <Copy size={11} className="text-text-tertiary group-hover:text-text-secondary transition-colors" />
          </button>
        </div>
        <StatusBadge status={license.status} />
      </div>

      {/* Temporal progress */}
      {license.status === "active" && (
        <div className="bg-surface-1 border border-border-subtle rounded-xl p-5">
          <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">
            Validade
          </p>
          <TimeProgress
            startDate={license.created_at}
            endDate={license.valid_until}
          />
          <p className="text-xs text-text-tertiary mt-2">
            {validFrom} → {validUntil}
          </p>
        </div>
      )}

      {/* Info table */}
      <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
        <InfoRow label="Produto" value={license.product_name} />
        <InfoRow
          label="Plano"
          value={license.billing_cycle === "monthly" ? "Mensal" : "Anual"}
        />
        <InfoRow
          label="Valor"
          value={`R$ ${parseFloat(license.amount).toFixed(2)}`}
          mono
        />
        <InfoRow label="Vigência" value={`${validFrom} até ${validUntil}`} />
        <InfoRow
          label="Dias restantes"
          value={license.status === "active" ? `${license.days_remaining} dias` : "—"}
          highlight={license.status === "active" && license.days_remaining <= 15}
        />
      </div>

      {/* Services */}
      <div>
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
          Serviços inclusos ({license.services.length})
        </h2>
        {license.services.length === 0 ? (
          <p className="text-sm text-text-tertiary">Nenhum serviço vinculado.</p>
        ) : (
          <div className="space-y-3">
            {license.services.map((sa) => (
              <ServiceCard key={sa.id} service={sa} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function InfoRow({
  label,
  value,
  mono,
  highlight,
}: {
  label: string;
  value: string;
  mono?: boolean;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between px-5 py-3.5">
      <span className="text-sm text-text-secondary">{label}</span>
      <span
        className={cn(
          "text-sm font-medium",
          mono ? "font-mono text-xs text-text-tertiary" : "text-text-primary",
          highlight && "text-warning"
        )}
      >
        {value}
      </span>
    </div>
  );
}

function ServiceCard({ service }: { service: ServiceAccess }) {
  const statusMap: Record<string, { variant: "success" | "info" | "warning" | "danger" | "muted"; label: string }> = {
    active:       { variant: "success", label: "Ativo" },
    provisioning: { variant: "info",    label: "Provisionando" },
    suspended:    { variant: "warning", label: "Suspenso" },
    failed:       { variant: "danger",  label: "Falhou" },
  };
  const config = statusMap[service.status] ?? { variant: "muted" as const, label: service.status };

  return (
    <div className="bg-surface-2 border border-border-subtle rounded-lg px-4 py-3.5 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-text-primary">{service.service_key}</p>
        {service.external_id && (
          <p className="text-xs text-text-tertiary font-mono mt-0.5">{service.external_id}</p>
        )}
        {service.error && (
          <p className="text-xs text-danger mt-1">{service.error}</p>
        )}
      </div>
      <Badge variant={config.variant} dot>
        {config.label}
      </Badge>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-8 max-w-2xl">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-8 w-1/2" />
      <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex justify-between px-5 py-3.5">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>
    </div>
  );
}
