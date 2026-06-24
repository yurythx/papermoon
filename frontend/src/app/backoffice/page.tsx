"use client";

import { useQuery } from "@tanstack/react-query";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { PageHeader } from "@/components/compound/page-header";
import {
  TrendingUp,
  Users,
  UserPlus,
  UserX,
  AlertTriangle,
  BarChart2,
  TrendingDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { MRRMetrics, APIUsageRow } from "@/types";

const SERVICE_COLORS: string[] = [
  "bg-brand-accent",
  "bg-info",
  "bg-warning",
  "bg-success",
  "bg-danger",
  "bg-service-whatsapp",
  "bg-text-tertiary",
];

function serviceColor(index: number) {
  return SERVICE_COLORS[index % SERVICE_COLORS.length];
}

export default function BackofficeMetricsPage() {
  const { data: metrics, isLoading: loadingMetrics } = useQuery<MRRMetrics>({
    queryKey: ["admin-metrics"],
    queryFn: adminService.getMetrics,
    staleTime: 60_000,
  });

  const { data: apiUsage = [], isLoading: loadingUsage } = useQuery<APIUsageRow[]>({
    queryKey: ["admin-api-usage"],
    queryFn: adminService.getAPIUsage,
    staleTime: 60_000,
  });

  const currency = (v: number) =>
    v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

  const churnRate = metrics?.churn_rate ?? 0;
  const atRisk = metrics?.at_risk_count ?? 0;
  const churnStatus: KpiStatus =
    churnRate >= 10 ? "danger" : churnRate >= 5 ? "warning" : "neutral";

  return (
    <div className="space-y-8">
      <PageHeader title="Métricas" description="Visão consolidada da plataforma" />

      {/* KPI cards — row 1: revenue */}
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <KpiCard
          label="MRR"
          value={loadingMetrics ? null : currency(metrics?.mrr ?? 0)}
          icon={TrendingUp}
          status="success"
        />
        <KpiCard
          label="ARR"
          value={loadingMetrics ? null : currency(metrics?.arr ?? 0)}
          icon={TrendingUp}
          status="info"
        />
        <KpiCard
          label="Clientes ativos"
          value={loadingMetrics ? null : String(metrics?.active_customers ?? 0)}
          icon={Users}
          status="neutral"
        />
        <KpiCard
          label="Novos este mês"
          value={loadingMetrics ? null : String(metrics?.new_customers ?? 0)}
          icon={UserPlus}
          status="neutral"
        />
      </div>

      {/* KPI cards — row 2: churn & risk */}
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <KpiCard
          label="Churn este mês"
          value={loadingMetrics ? null : String(metrics?.churned_customers ?? 0)}
          icon={UserX}
          status={churnStatus}
        />
        <KpiCard
          label="Taxa de churn"
          value={loadingMetrics ? null : `${churnRate.toFixed(1)}%`}
          icon={TrendingDown}
          status={churnStatus}
          sub={churnRate >= 5 ? "Acima do limite saudável (5%)" : undefined}
        />
        <KpiCard
          label="Em risco"
          value={loadingMetrics ? null : String(atRisk)}
          icon={AlertTriangle}
          status={atRisk > 0 ? "warning" : "neutral"}
          sub={atRisk > 0 ? "Suspensos há mais de 7 dias" : undefined}
        />
        <KpiCard
          label="Uso de API"
          value={loadingMetrics ? null : `${apiUsage.length} clientes`}
          icon={BarChart2}
          status="neutral"
        />
      </div>

      {/* Monthly revenue chart + Revenue by plan — side by side on wide screens */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Revenue trend */}
        <div className="xl:col-span-2 bg-surface-1 border border-border-subtle rounded-xl p-6">
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-5">
            Receita mensal (12 meses)
          </h2>
          {loadingMetrics ? (
            <Skeleton className="h-32 w-full" />
          ) : metrics?.monthly_revenue && metrics.monthly_revenue.length > 0 ? (
            <RevenueBars data={metrics.monthly_revenue} />
          ) : (
            <p className="text-sm text-text-tertiary text-center py-8">
              Nenhuma receita registrada ainda.
            </p>
          )}
        </div>

        {/* Revenue by plan */}
        <div className="bg-surface-1 border border-border-subtle rounded-xl p-6">
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-5">
            Receita por plano
          </h2>
          {loadingMetrics ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
            </div>
          ) : metrics?.revenue_by_plan && metrics.revenue_by_plan.length > 0 ? (
            <RevenuePlanBars data={metrics.revenue_by_plan} currency={currency} />
          ) : (
            <p className="text-sm text-text-tertiary text-center py-8">
              Ainda nao ha receita consolidada por plano neste periodo.
            </p>
          )}
        </div>
      </div>

      {/* API usage table */}
      <div className="bg-surface-1 border border-border-subtle rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-border-subtle flex items-center justify-between">
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
            Uso de API por cliente
          </h2>
          {apiUsage.some((r) => r.usage_pct >= 80) && (
            <span className="text-xs text-warning flex items-center gap-1">
              <AlertTriangle size={11} />
              {apiUsage.filter((r) => r.usage_pct >= 80).length} cliente(s) acima de 80%
            </span>
          )}
        </div>
        {loadingUsage ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
          </div>
        ) : apiUsage.length === 0 ? (
          <div className="p-8 text-center text-sm text-text-tertiary">
            Nenhum dado de uso disponível.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[440px]">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                    Cliente
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                    Usado
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                    Limite
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider w-48">
                    Uso
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {apiUsage.map((row) => (
                  <tr key={row.customer_id} className="hover:bg-surface-2 transition-colors">
                    <td className="px-6 py-3.5 text-text-primary font-medium">{row.company_name}</td>
                    <td className="px-6 py-3.5 text-right text-text-secondary tabular-nums">
                      {row.used_api_calls.toLocaleString("pt-BR")}
                    </td>
                    <td className="px-6 py-3.5 text-right text-text-secondary tabular-nums">
                      {row.max_api_calls.toLocaleString("pt-BR")}
                    </td>
                    <td className="px-6 py-3.5">
                      <div className="flex items-center gap-3">
                        <Progress
                          value={Math.min(row.usage_pct, 100)}
                          variant={row.usage_pct >= 90 ? "danger" : row.usage_pct >= 70 ? "warning" : "default"}
                          className="flex-1"
                        />
                        <span className="text-xs text-text-tertiary w-10 text-right tabular-nums">
                          {row.usage_pct}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

type KpiStatus = "success" | "info" | "warning" | "danger" | "neutral";

const kpiStatusClasses: Record<KpiStatus, { card: string; icon: string; value: string }> = {
  success: { card: "border-success/20 bg-success-muted", icon: "text-success", value: "text-success" },
  info:    { card: "border-info/20 bg-info-muted",       icon: "text-info",    value: "text-info" },
  warning: { card: "border-warning/20 bg-warning-muted", icon: "text-warning", value: "text-warning" },
  danger:  { card: "border-danger/20 bg-danger-muted",   icon: "text-danger",  value: "text-danger" },
  neutral: { card: "border-border-subtle bg-surface-1",  icon: "text-text-tertiary", value: "text-text-primary" },
};

function KpiCard({
  label,
  value,
  icon: Icon,
  sub,
  status = "neutral",
}: {
  label: string;
  value: string | null;
  icon: React.ElementType;
  sub?: string;
  status?: KpiStatus;
}) {
  const c = kpiStatusClasses[status];
  return (
    <div className={`rounded-xl p-5 border ${c.card}`}>
      <div className="flex items-start justify-between mb-2">
        <p className="text-xs text-text-secondary font-medium">{label}</p>
        <Icon size={15} className={c.icon} />
      </div>
      {value === null ? (
        <Skeleton className="h-7 w-28" />
      ) : (
        <p className={`text-2xl font-bold tabular-nums ${c.value}`}>{value}</p>
      )}
      {sub && (
        <p className={cn("text-xs mt-1", status === "danger" ? "text-danger" : "text-warning")}>
          {sub}
        </p>
      )}
    </div>
  );
}

function RevenueBars({ data }: { data: { month: string; revenue: number }[] }) {
  const max = Math.max(...data.map((d) => d.revenue), 1);

  return (
    <div className="flex items-end gap-1 h-32">
      {data.map((d) => {
        const pct = (d.revenue / max) * 100;
        const label = new Date(d.month + "-01").toLocaleDateString("pt-BR", {
          month: "short",
          year: "2-digit",
        });
        return (
          <div key={d.month} className="flex-1 flex flex-col items-center gap-1 group">
            <div className="relative w-full flex items-end justify-center" style={{ height: "100px" }}>
              <div
                className="w-full bg-brand-accent/70 rounded-t group-hover:bg-brand-accent transition-colors"
                style={{ height: `${pct}%`, minHeight: "4px" }}
                title={d.revenue.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
              />
            </div>
            <span className="text-xs text-text-tertiary truncate w-full text-center">{label}</span>
          </div>
        );
      })}
    </div>
  );
}

function RevenuePlanBars({
  data,
  currency,
}: {
  data: { plan: string; revenue: number; customer_count: number }[];
  currency: (v: number) => string;
}) {
  const max = Math.max(...data.map((d) => d.revenue), 1);

  return (
    <div className="space-y-3">
      {data.map((d, idx) => {
        const pct = (d.revenue / max) * 100;
        return (
          <div key={d.plan} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-primary font-medium">{d.plan}</span>
              <span className="text-text-tertiary tabular-nums">
                {currency(d.revenue)}{" "}
                <span className="text-text-tertiary">({d.customer_count})</span>
              </span>
            </div>
            <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all duration-500", serviceColor(idx))}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
