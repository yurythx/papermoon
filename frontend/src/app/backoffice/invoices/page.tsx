"use client";

import axios from "axios";
import { useId, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/compound/status-badge";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { Receipt, Plus, ExternalLink } from "lucide-react";
import type { AdminCustomer, AdminInvoice } from "@/types";

const INVOICE_TYPE_LABEL: Record<string, string> = {
  subscription: "Assinatura",
  implementation: "Implantação",
  support: "Suporte",
};

export default function BackofficeInvoicesPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(1);
  const [deleteTarget, setDeleteTarget] = useState<AdminInvoice | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-invoices", statusFilter, typeFilter, page],
    queryFn: () =>
      adminService.listInvoices({
        status: statusFilter || undefined,
        invoice_type: typeFilter || undefined,
        page,
      }),
    staleTime: 30_000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminService.softDeleteInvoice(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-invoices"] });
      setDeleteTarget(null);
      toast.success("Fatura removida.");
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao remover fatura.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const invoices = data?.results ?? [];
  const numPages = data?.num_pages ?? 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Faturas"
        description="Todas as faturas da plataforma"
        actions={
          <Button variant="primary" size="sm" onClick={() => setShowCreate(true)}>
            <Plus size={13} className="mr-1.5" />
            Nova fatura
          </Button>
        }
      />

      <div className="flex gap-3 items-center flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="bg-surface-1 border border-border-default text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent/50"
        >
          <option value="">Todos os status</option>
          <option value="pending">Pendente</option>
          <option value="paid">Pago</option>
          <option value="overdue">Vencido</option>
          <option value="cancelled">Cancelado</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
          className="bg-surface-1 border border-border-default text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent/50"
        >
          <option value="">Todos os tipos</option>
          <option value="subscription">Assinatura</option>
          <option value="implementation">Implantação</option>
          <option value="support">Suporte</option>
        </select>

        {data && (
          <p className="text-sm text-text-tertiary">
            {data.count} fatura{data.count !== 1 ? "s" : ""}
          </p>
        )}
      </div>

      <div className="bg-surface-1 border border-border-subtle rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : invoices.length === 0 ? (
          <EmptyState icon={Receipt} title="Nenhuma fatura encontrada" description="Tente ajustar os filtros." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[700px]">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Cliente</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Tipo</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Pagamento</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Valor</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Vencimento</th>
                  <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Criado em</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-surface-2 transition-colors">
                    <td className="px-5 py-3.5 font-medium text-text-primary">{inv.company_name}</td>
                    <td className="px-5 py-3.5">
                      <span className="text-xs text-text-secondary">
                        {INVOICE_TYPE_LABEL[inv.invoice_type] ?? inv.invoice_type}
                      </span>
                      {inv.description && (
                        <p className="text-xs text-text-tertiary/70 truncate max-w-[160px]" title={inv.description}>
                          {inv.description}
                        </p>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="text-xs text-text-secondary">
                        {BILLING_TYPE_LABEL[inv.billing_type] ?? inv.billing_type}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-text-secondary tabular-nums">
                      {Number(inv.amount).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="px-5 py-3.5 text-text-secondary">
                      {new Date(inv.due_date).toLocaleDateString("pt-BR")}
                    </td>
                    <td className="px-5 py-3.5 text-text-tertiary text-xs">
                      {new Date(inv.created_at).toLocaleDateString("pt-BR")}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {inv.payment_url && (inv.status === "pending" || inv.status === "overdue") && (
                          <a
                            href={inv.payment_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs text-brand-accent hover:underline font-medium"
                            title="Link de pagamento Asaas"
                          >
                            Link <ExternalLink size={11} />
                          </a>
                        )}
                        <Button size="sm" variant="ghost" onClick={() => setDeleteTarget(inv)}>
                          Remover
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {numPages > 1 && (
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <span>{data?.count} fatura{data?.count !== 1 ? "s" : ""}</span>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" disabled={page === 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
              Anterior
            </Button>
            <span className="px-3 text-text-tertiary">{page} / {numPages}</span>
            <Button variant="secondary" size="sm" disabled={page === numPages} onClick={() => setPage((p) => Math.min(numPages, p + 1))}>
              Próxima
            </Button>
          </div>
        </div>
      )}

      {deleteTarget && (
        <DeleteInvoiceDialog
          invoice={deleteTarget}
          loading={deleteMutation.isPending}
          onCancel={() => setDeleteTarget(null)}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
        />
      )}

      {showCreate && (
        <CreateInvoiceModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            qc.invalidateQueries({ queryKey: ["admin-invoices"] });
            setShowCreate(false);
          }}
        />
      )}
    </div>
  );
}

function DeleteInvoiceDialog({
  invoice,
  loading,
  onConfirm,
  onCancel,
}: {
  invoice: AdminInvoice;
  loading: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const titleId = useId();
  const descriptionId = useId();

  return (
    <Dialog onClose={onCancel} titleId={titleId} descriptionId={descriptionId} className="max-w-sm p-6">
            <h3 id={titleId} className="text-base font-semibold text-text-primary">Remover fatura</h3>
            <p id={descriptionId} className="text-sm text-text-secondary mt-2">
              Fatura de{" "}
              <span className="font-medium text-text-primary">
                {Number(invoice.amount).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
              </span>{" "}
              de <span className="font-medium text-text-primary">{invoice.company_name}</span> será
              ocultada da plataforma (soft-delete).
            </p>
            <div className="flex gap-3 mt-6 justify-end">
              <Button variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
                Cancelar
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={onConfirm}
                disabled={loading}
                loading={loading}
              >
                Remover
              </Button>
            </div>
    </Dialog>
  );
}

const BILLING_TYPE_LABEL: Record<string, string> = {
  BOLETO: "Boleto bancário",
  PIX: "Pix",
  CREDIT_CARD: "Cartão de crédito",
};

function CreateInvoiceModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [customerId, setCustomerId] = useState("");
  const [invoiceType, setInvoiceType] = useState<"implementation" | "support">("support");
  const [billingType, setBillingType] = useState<"BOLETO" | "PIX" | "CREDIT_CARD">("BOLETO");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [description, setDescription] = useState("");

  const { data: customers = [] } = useQuery<AdminCustomer[]>({
    queryKey: ["admin-customers-all"],
    queryFn: () => adminService.listCustomers({ page: 1 }).then((r) => r.results),
    staleTime: 60_000,
  });

  const mutation = useMutation({
    mutationFn: () =>
      adminService.createInvoice({
        customer_id: customerId,
        invoice_type: invoiceType,
        billing_type: billingType,
        amount,
        due_date: dueDate,
        description,
      }),
    onSuccess: () => {
      toast.success("Fatura criada.");
      onCreated();
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao criar fatura.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const canSubmit = customerId && amount && dueDate;
  const titleId = useId();

  return (
    <Dialog onClose={onClose} titleId={titleId} className="max-w-md space-y-4 p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary">Nova fatura avulsa</h3>

        <div className="space-y-3">
          <div>
            <label className="block text-xs text-text-tertiary mb-1">Cliente *</label>
            <select
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus"
            >
              <option value="">Selecione o cliente</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>{c.company_name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-text-tertiary mb-1">Tipo *</label>
              <select
                value={invoiceType}
                onChange={(e) => setInvoiceType(e.target.value as "implementation" | "support")}
                className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus"
              >
                <option value="support">Suporte</option>
                <option value="implementation">Implantação</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-text-tertiary mb-1">Forma de pagamento *</label>
              <select
                value={billingType}
                onChange={(e) => setBillingType(e.target.value as "BOLETO" | "PIX" | "CREDIT_CARD")}
                className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus"
              >
                {Object.entries(BILLING_TYPE_LABEL).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-text-tertiary mb-1">Valor (R$) *</label>
              <Input
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="500.00"
                type="number"
                min="0"
                step="0.01"
              />
            </div>
            <div>
              <label className="block text-xs text-text-tertiary mb-1">Vencimento *</label>
              <Input
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                type="date"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-text-tertiary mb-1">Descrição</label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="ex: Chamado #42 — ajuste de configuração GLPI"
            />
          </div>
        </div>

        <div className="flex gap-3 justify-end pt-2">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="sm"
            disabled={!canSubmit || mutation.isPending}
            loading={mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            Criar fatura
          </Button>
        </div>
    </Dialog>
  );
}
