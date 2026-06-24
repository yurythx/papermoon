"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { ShieldCheck } from "lucide-react";

const RESOURCE_TYPES = ["Customer", "Subscription", "Invoice", "ApiKey", "License"];

export default function BackofficeAuditPage() {
  const [resourceType, setResourceType] = useState("");
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-audit", resourceType, action, page],
    queryFn: () =>
      adminService.getAuditLogs({
        resource_type: resourceType || undefined,
        action: action || undefined,
        page,
      }),
    staleTime: 30_000,
  });

  const logs = data?.results ?? [];
  const totalPages = data ? Math.ceil(data.count / 20) : 1;

  return (
    <div className="space-y-6">
      <PageHeader title="Audit Log" description="Trilha de auditoria de todas as ações na plataforma" />

      <div className="flex gap-3">
        <select
          value={resourceType}
          onChange={(e) => { setResourceType(e.target.value); setPage(1); }}
          className="bg-surface-1 border border-border-default text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent/50"
        >
          <option value="">Todos os recursos</option>
          {RESOURCE_TYPES.map((rt) => (
            <option key={rt} value={rt}>{rt}</option>
          ))}
        </select>
        <Input
          type="text"
          placeholder="Filtrar por ação (ex: customer.created)"
          value={action}
          onChange={(e) => { setAction(e.target.value); setPage(1); }}
          className="flex-1"
        />
      </div>

      <div className="bg-surface-1 border border-border-subtle rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : logs.length === 0 ? (
          <EmptyState icon={ShieldCheck} title="Nenhum registro encontrado" description="Tente ajustar os filtros." />
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[560px]">
            <thead>
              <tr className="border-b border-border-subtle">
                <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Data</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Ação</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Recurso</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Usuário</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {logs.map((log) => {
                const date = new Date(log.created_at).toLocaleString("pt-BR", {
                  day: "2-digit",
                  month: "2-digit",
                  year: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit",
                });
                return (
                  <tr key={log.id} className="hover:bg-surface-2 transition-colors">
                    <td className="px-6 py-3.5 text-text-tertiary text-xs whitespace-nowrap">{date}</td>
                    <td className="px-6 py-3.5">
                      <code className="text-xs bg-surface-2 border border-border-subtle px-1.5 py-0.5 rounded text-text-secondary font-mono">
                        {log.action}
                      </code>
                    </td>
                    <td className="px-6 py-3.5 text-text-secondary">
                      <span className="font-medium">{log.resource_type}</span>
                      <span className="text-text-tertiary ml-1 font-mono text-xs">
                        {log.resource_id.slice(0, 8)}…
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-text-tertiary text-xs">{log.user ?? "—"}</td>
                    <td className="px-6 py-3.5 text-text-tertiary font-mono text-xs">{log.ip_address ?? "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <span>{data?.count} registro{data?.count !== 1 ? "s" : ""}</span>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" disabled={page === 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
              Anterior
            </Button>
            <span className="px-3 text-text-tertiary">{page} / {totalPages}</span>
            <Button variant="secondary" size="sm" disabled={page === totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>
              Próxima
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
