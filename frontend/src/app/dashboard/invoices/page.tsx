"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { invoiceService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/compound/status-badge";
import { PageHeader } from "@/components/compound/page-header";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/compound/empty-state";
import { AlertTriangle, Download, Receipt } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Invoice } from "@/types";

const STATUS_OPTS = [
  { value: "", label: "Todas" },
  { value: "pending", label: "Pendentes" },
  { value: "paid", label: "Pagas" },
  { value: "overdue", label: "Vencidas" },
  { value: "cancelled", label: "Canceladas" },
];

export default function InvoicesPage() {
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["invoices", status, page],
    queryFn: () => invoiceService.list({ status: status || undefined, page }),
  });

  const { data: overdueData } = useQuery({
    queryKey: ["invoices-overdue-banner"],
    queryFn: () => invoiceService.list({ status: "overdue", page: 1 }),
    staleTime: 60_000,
  });

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const overdueInvoices = overdueData?.results ?? [];
  const maxDaysOverdue = overdueInvoices.reduce((max, inv) => {
    const days = Math.floor((today.getTime() - new Date(inv.due_date).getTime()) / 86_400_000);
    return Math.max(max, days);
  }, 0);
  const showDangerBanner = maxDaysOverdue >= 7;
  const showWarningBanner = !showDangerBanner && maxDaysOverdue >= 3;

  const exportMutation = useMutation({
    mutationFn: () => invoiceService.exportCsv(status ? { status } : undefined),
    onSuccess: () => toast.success("CSV exportado com sucesso."),
    onError: () => toast.error("Erro ao exportar faturas."),
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Faturas"
        description="Histórico de cobranças da sua conta"
        actions={
          <Button
            variant="secondary"
            size="sm"
            loading={exportMutation.isPending}
            onClick={() => exportMutation.mutate()}
          >
            <Download size={13} className="mr-1.5" />
            Exportar CSV
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {STATUS_OPTS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => { setStatus(opt.value); setPage(1); }}
            className={cn(
              "text-xs px-3 py-1.5 rounded-full border transition-colors",
              status === opt.value
                ? "bg-brand-accent text-slate-950 border-brand-accent"
                : "bg-surface-2 text-text-secondary border-border-default hover:border-border-focus hover:text-text-primary"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {showDangerBanner && (
        <div className="flex items-start gap-3 bg-danger/10 border border-danger/30 text-danger rounded-xl px-4 py-3 text-sm">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <p>
            <span className="font-semibold">Suspensão iminente.</span> Você tem fatura(s) vencida(s) há {maxDaysOverdue} dias.
            Regularize o pagamento para evitar a suspensão dos serviços.
          </p>
        </div>
      )}

      {showWarningBanner && (
        <div className="flex items-start gap-3 bg-warning/10 border border-warning/30 text-warning rounded-xl px-4 py-3 text-sm">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <p>
            <span className="font-semibold">Fatura vencida.</span> Você tem fatura(s) vencida(s) há {maxDaysOverdue} dias.
            Regularize o pagamento para evitar a suspensão dos serviços em {7 - maxDaysOverdue} dias.
          </p>
        </div>
      )}

      {isLoading ? (
        <TableSkeleton />
      ) : !data?.results.length ? (
        <EmptyState
          title="Nenhuma fatura encontrada"
          icon={Receipt}
          description="As cobranças aparecem aqui após a ativação de um produto."
        />
      ) : (
        <>
          <div className="bg-surface-1 border border-border-subtle rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[520px]">
                <thead className="border-b border-border-subtle">
                  <tr>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                      Vencimento
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                      Valor
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {data.results.map((invoice) => (
                    <InvoiceRow key={invoice.id} invoice={invoice} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-text-tertiary">
              {data.count} fatura{data.count !== 1 ? "s" : ""}
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={!data.previous}
                onClick={() => setPage((p) => p - 1)}
              >
                Anterior
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={!data.next}
                onClick={() => setPage((p) => p + 1)}
              >
                Próxima
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

const INVOICE_TYPE_LABEL: Record<string, string> = {
  subscription: "Assinatura",
  implementation: "Implantação",
  support: "Suporte",
};

function InvoiceRow({ invoice }: { invoice: Invoice }) {
  return (
    <tr className="hover:bg-surface-2 transition-colors">
      <td className="px-5 py-3.5 text-text-secondary tabular-nums">
        {new Date(invoice.due_date).toLocaleDateString("pt-BR")}
      </td>
      <td className="px-5 py-3.5">
        <span className="text-xs text-text-tertiary">
          {INVOICE_TYPE_LABEL[invoice.invoice_type] ?? invoice.invoice_type}
        </span>
        {invoice.description && (
          <p className="text-xs text-text-tertiary/70 truncate max-w-[180px]" title={invoice.description}>
            {invoice.description}
          </p>
        )}
      </td>
      <td className="px-5 py-3.5 font-semibold text-text-primary tabular-nums">
        R$ {parseFloat(invoice.amount).toFixed(2)}
      </td>
      <td className="px-5 py-3.5">
        <StatusBadge status={invoice.status} />
      </td>
      <td className="px-5 py-3.5 text-right">
        {invoice.payment_url && invoice.status === "pending" && (
          <a
            href={invoice.payment_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-accent hover:underline font-medium"
          >
            Pagar →
          </a>
        )}
      </td>
    </tr>
  );
}

function TableSkeleton() {
  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl overflow-hidden">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex gap-4 px-5 py-3.5 border-b border-border-subtle">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}
