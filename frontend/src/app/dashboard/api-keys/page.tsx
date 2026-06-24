"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { apiKeyService, customerService, type DailyUsagePoint } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { Fingerprint, Copy, CheckCheck, Info, Zap, AlertTriangle, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ApiKey, ApiQuota } from "@/types";

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [newKeyId, setNewKeyId] = useState<string | null>(null);

  const { data: keys = [], isLoading } = useQuery<ApiKey[]>({
    queryKey: ["api-keys"],
    queryFn: apiKeyService.list,
  });

  const { data: quota, isLoading: quotaLoading } = useQuery<ApiQuota>({
    queryKey: ["api-quota"],
    queryFn: customerService.getQuota,
    staleTime: 60_000,
  });

  const { data: usageHistory = [], isLoading: usageLoading } = useQuery<DailyUsagePoint[]>({
    queryKey: ["api-usage-history"],
    queryFn: () => apiKeyService.usageHistory(30),
    staleTime: 300_000,
  });

  const createMutation = useMutation({
    mutationFn: apiKeyService.create,
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setNewKeyId(created.id);
      toast.success("API Key gerada com sucesso.");
    },
    onError: () => toast.error("Erro ao gerar API Key."),
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => apiKeyService.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      setRevokingId(null);
      toast.success("API Key revogada.");
    },
    onError: () => { setRevokingId(null); toast.error("Erro ao revogar."); },
  });

  function handleRevoke(id: string) {
    setRevokingId(id);
    revokeMutation.mutate(id);
  }

  const activeKeys = keys.filter((k) => k.is_active);
  const revokedKeys = keys.filter((k) => !k.is_active);

  return (
    <div className="space-y-8 max-w-2xl">
      <PageHeader
        title="API Keys"
        description="Chaves de acesso para integrações externas"
        actions={
          <Button
            variant="primary"
            size="sm"
            loading={createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            Gerar nova chave
          </Button>
        }
      />

      {/* Quota card */}
      {quotaLoading ? (
        <Skeleton className="h-24 w-full rounded-xl" />
      ) : quota ? (
        <QuotaCard quota={quota} />
      ) : null}

      {/* Daily usage chart */}
      {usageLoading ? (
        <Skeleton className="h-36 w-full rounded-xl" />
      ) : (
        <DailyUsageChart data={usageHistory} />
      )}

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2].map((i) => <Skeleton key={i} className="h-16 w-full rounded-xl" />)}
        </div>
      ) : (
        <>
          {activeKeys.length === 0 ? (
            <EmptyState
              title="Nenhuma API Key ativa"
              icon={Fingerprint}
              description="Gere uma chave para integrar com o n8n ou outros sistemas."
            />
          ) : (
            <div className="space-y-2">
              <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                Ativas ({activeKeys.length})
              </h2>
              {activeKeys.map((k) => (
                <KeyRow
                  key={k.id}
                  apiKey={k}
                  highlight={k.id === newKeyId}
                  onRevoke={() => handleRevoke(k.id)}
                  revoking={revokingId === k.id}
                />
              ))}
            </div>
          )}

          {revokedKeys.length > 0 && (
            <div className="space-y-2">
              <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                Revogadas ({revokedKeys.length})
              </h2>
              {revokedKeys.map((k) => <KeyRow key={k.id} apiKey={k} />)}
            </div>
          )}
        </>
      )}

      {/* Usage info */}
      <div className="bg-surface-2 border border-border-subtle rounded-xl p-4 flex gap-3">
        <Info size={15} className="text-info shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-text-primary">Como usar sua API Key</p>
          <p className="text-xs text-text-secondary mt-1">
            Passe a chave via query param:{" "}
            <code className="bg-surface-3 px-1.5 py-0.5 rounded font-mono text-xs text-info">
              GET /api/v1/licensing/validate-key/?key=SUA_CHAVE
            </code>
          </p>
          <p className="text-xs text-text-tertiary mt-1">
            O endpoint retorna{" "}
            <code className="bg-surface-3 px-1.5 py-0.5 rounded font-mono text-xs">
              {"{ valid, quota_remaining }"}
            </code>{" "}
            e pode ser chamado pelo n8n antes de cada automação.
          </p>
        </div>
      </div>
    </div>
  );
}

function QuotaCard({ quota }: { quota: ApiQuota }) {
  const pct = quota.usage_pct ?? 0;
  const isWarning = pct >= 80 && pct < 95;
  const isDanger = pct >= 95;

  const barColor = isDanger
    ? "bg-danger"
    : isWarning
    ? "bg-warning"
    : "bg-brand-accent";

  const daysUntilReset = quota.reset_at
    ? Math.max(0, Math.ceil((new Date(quota.reset_at).getTime() - Date.now()) / 86_400_000))
    : null;

  const planLabel = quota.plan_name
    ? `Plano ${quota.plan_name}${quota.billing_cycle === "annual" ? " (anual)" : ""}`
    : "Plano ativo";

  return (
    <div
      className={cn(
        "bg-surface-1 border rounded-xl p-4 space-y-3",
        isDanger ? "border-danger/40" : isWarning ? "border-warning/40" : "border-border-subtle"
      )}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Zap size={14} className={isDanger ? "text-danger" : isWarning ? "text-warning" : "text-brand-accent"} />
          <span className="text-sm font-semibold text-text-primary">{planLabel}</span>
        </div>
        <div className="flex items-center gap-2">
          {(isWarning || isDanger) && (
            <AlertTriangle size={13} className={isDanger ? "text-danger" : "text-warning"} />
          )}
          <span className="text-xs text-text-tertiary tabular-nums">
            {quota.used_api_calls.toLocaleString("pt-BR")} /{" "}
            {quota.max_api_calls.toLocaleString("pt-BR")} chamadas
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", barColor)}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>

      <div className="flex items-center justify-between">
        <span
          className={cn(
            "text-xs",
            isDanger ? "text-danger font-medium" : isWarning ? "text-warning font-medium" : "text-text-tertiary"
          )}
        >
          {isDanger
            ? "Quota esgotada — novas chamadas serão bloqueadas"
            : isWarning
            ? `${pct.toFixed(1)}% usado — considere fazer upgrade do plano`
            : `${pct.toFixed(1)}% utilizado`}
        </span>
        {daysUntilReset !== null && (
          <span className="text-xs text-text-tertiary">
            Renova em {daysUntilReset} dia{daysUntilReset !== 1 ? "s" : ""}
          </span>
        )}
      </div>
    </div>
  );
}

function KeyRow({
  apiKey,
  highlight,
  onRevoke,
  revoking,
}: {
  apiKey: ApiKey;
  highlight?: boolean;
  onRevoke?: () => void;
  revoking?: boolean;
}) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(apiKey.key).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  const createdAt = new Date(apiKey.created_at).toLocaleDateString("pt-BR");
  const revokedAt = apiKey.revoked_at
    ? new Date(apiKey.revoked_at).toLocaleDateString("pt-BR")
    : null;

  return (
    <div
      className={cn(
        "bg-surface-1 border rounded-xl px-4 py-3 flex items-center gap-3 transition-colors",
        highlight ? "border-success/40 bg-success-muted" : "border-border-subtle",
        !apiKey.is_active && "opacity-60"
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <code className="text-xs font-mono text-text-secondary truncate max-w-xs">
            {apiKey.is_active ? apiKey.key : apiKey.key.slice(0, 8) + "••••••••••"}
          </code>
          <Badge variant={apiKey.is_active ? "success" : "muted"} dot>
            {apiKey.is_active ? "ativa" : "revogada"}
          </Badge>
        </div>
        <p className="text-xs text-text-tertiary mt-0.5">
          Criada em {createdAt}
          {revokedAt ? ` · Revogada em ${revokedAt}` : ""}
        </p>
      </div>

      {apiKey.is_active && (
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="xs" onClick={copy}>
            {copied ? <CheckCheck size={13} className="text-success" /> : <Copy size={13} />}
            {copied ? "Copiado" : "Copiar"}
          </Button>
          <Button
            variant="ghost"
            size="xs"
            className="text-danger hover:text-danger hover:bg-danger-muted"
            disabled={revoking}
            loading={revoking}
            onClick={onRevoke}
          >
            Revogar
          </Button>
        </div>
      )}
    </div>
  );
}

function DailyUsageChart({ data }: { data: DailyUsagePoint[] }) {
  const total = data.reduce((s, d) => s + d.calls, 0);
  const peak = Math.max(...data.map((d) => d.calls), 1);

  if (total === 0) {
    return (
      <div className="bg-surface-1 border border-border-subtle rounded-xl p-4 flex items-center gap-3">
        <BarChart2 size={15} className="text-text-tertiary shrink-0" />
        <p className="text-sm text-text-tertiary">0 chamadas nos últimos 30 dias</p>
      </div>
    );
  }

  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart2 size={14} className="text-brand-accent" />
          <span className="text-sm font-semibold text-text-primary">Uso diário</span>
        </div>
        <span className="text-xs text-text-tertiary tabular-nums">
          {total.toLocaleString("pt-BR")} chamadas em 30 dias
        </span>
      </div>

      {/* Bars */}
      <div className="flex items-end gap-0.5 h-16">
        {data.map((point) => {
          const heightPct = (point.calls / peak) * 100;
          return (
            <div
              key={point.date}
              className="flex-1 flex flex-col justify-end group relative"
              title={`${point.date}: ${point.calls.toLocaleString("pt-BR")} chamadas`}
            >
              <div
                className="w-full rounded-sm bg-brand-accent/60 group-hover:bg-brand-accent transition-colors"
                style={{ height: `${Math.max(heightPct, point.calls > 0 ? 4 : 0)}%` }}
              />
              {/* Tooltip */}
              <div className="absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 hidden group-hover:block z-10 pointer-events-none">
                <div className="bg-surface-3 border border-border-subtle rounded px-2 py-1 text-xs text-text-primary whitespace-nowrap shadow-sm">
                  {point.calls.toLocaleString("pt-BR")}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Date labels — every 7 days */}
      <div className="flex justify-between">
        {data
          .filter((_, i) => i === 0 || i === 14 || i === data.length - 1)
          .map((point) => (
            <span key={point.date} className="text-[10px] text-text-tertiary tabular-nums">
              {new Date(point.date + "T00:00:00").toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "2-digit",
              })}
            </span>
          ))}
      </div>
    </div>
  );
}
