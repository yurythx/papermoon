"use client";

import { useQuery } from "@tanstack/react-query";
import { adminService } from "@/lib/services";
import { PageHeader } from "@/components/compound/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, AlertTriangle, RefreshCw, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { cardClass, type CardTone } from "@/components/ui/card";

type ServiceStatus = "ok" | "degraded" | "error" | "unknown";

function StatusIcon({ status }: { status: ServiceStatus }) {
  if (status === "ok") return <CheckCircle2 size={18} className="text-success" />;
  if (status === "degraded") return <AlertTriangle size={18} className="text-warning" />;
  if (status === "error") return <XCircle size={18} className="text-danger" />;
  return <AlertTriangle size={18} className="text-text-tertiary" />;
}

function statusLabel(s: ServiceStatus): string {
  return { ok: "Operacional", degraded: "Degradado", error: "Falha", unknown: "Desconhecido" }[s];
}

const STATUS_TONE: Record<ServiceStatus, CardTone> = {
  ok: "success",
  degraded: "warning",
  error: "danger",
  unknown: "neutral",
};

function statusTone(s: ServiceStatus): CardTone {
  return STATUS_TONE[s];
}

const SERVICE_NAMES: Record<string, string> = {
  db: "PostgreSQL",
  redis: "Redis",
  celery: "Celery Workers",
};

export default function HealthPage() {
  const {
    data,
    isLoading,
    isError,
    dataUpdatedAt,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ["health-status"],
    queryFn: adminService.getHealthStatus,
    refetchInterval: 30_000,
    retry: false,
  });

  const services: { key: string; status: ServiceStatus }[] = isError
    ? [
        { key: "db", status: "unknown" },
        { key: "redis", status: "unknown" },
        { key: "celery", status: "unknown" },
      ]
    : Object.entries(data ?? {}).map(([key, val]) => ({
        key,
        status: (["ok", "degraded", "error"].includes(val) ? val : "unknown") as ServiceStatus,
      }));

  const allOk = !isError && services.every((s) => s.status === "ok");
  const anyError = isError || services.some((s) => s.status === "error");
  const anyDegraded = services.some((s) => s.status === "degraded");

  const overallStatus: ServiceStatus = anyError
    ? "error"
    : anyDegraded
    ? "degraded"
    : allOk
    ? "ok"
    : "unknown";

  const updatedAt = dataUpdatedAt
    ? new Date(dataUpdatedAt).toLocaleTimeString("pt-BR")
    : null;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Status da Plataforma"
        description="Saúde dos serviços de infraestrutura em tempo real"
        actions={
          <Button variant="secondary" size="sm" loading={isFetching} onClick={() => refetch()}>
            <RefreshCw size={13} className="mr-1.5" />
            Atualizar
          </Button>
        }
      />

      {/* Overall banner */}
      <div className={cardClass({ tone: statusTone(overallStatus), className: "flex items-center gap-3 px-5 py-4" })}>
        <Activity size={20} className={anyError ? "text-danger" : anyDegraded ? "text-warning" : "text-success"} />
        <div>
          <p className="font-semibold text-text-primary">
            {anyError
              ? "Um ou mais serviços estão com falha"
              : anyDegraded
              ? "Serviços operando em modo degradado"
              : allOk
              ? "Todos os serviços estão operacionais"
              : "Verificando status…"}
          </p>
          {updatedAt && (
            <p className="text-xs text-text-tertiary mt-0.5">Última verificação: {updatedAt} · atualiza a cada 30s</p>
          )}
        </div>
      </div>

      {/* Service cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {isLoading
          ? [1, 2, 3].map((i) => (
              <div key={i} className={cardClass({ className: "space-y-3" })}>
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-20" />
              </div>
            ))
          : services.map(({ key, status }) => (
              <div key={key} className={cardClass({ tone: statusTone(status), className: "flex items-start gap-3" })}>
                <StatusIcon status={status} />
                <div>
                  <p className="text-sm font-semibold text-text-primary">
                    {SERVICE_NAMES[key] ?? key}
                  </p>
                  <p className={cn(
                    "text-xs mt-0.5 font-medium",
                    status === "ok" ? "text-success" : status === "degraded" ? "text-warning" : "text-danger"
                  )}>
                    {statusLabel(status)}
                  </p>
                </div>
              </div>
            ))}
      </div>

      {isError && (
        <div className={cardClass({ tone: "danger", className: "text-sm text-danger" })}>
          Não foi possível contatar o backend. Verifique se o serviço está rodando.
        </div>
      )}
    </div>
  );
}
