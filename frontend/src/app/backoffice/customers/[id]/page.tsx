"use client";

import { useId, useState } from "react";
import Link from "next/link";
import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Building2, ChevronLeft, Pencil, Check, X } from "lucide-react";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/compound/status-badge";
import type { AdminCustomer, AdminInvoice, CustomerQuota, Subscription } from "@/types";

type Action = "suspend" | "reactivate" | "cancel";

const ACTION_META: Record<Action, { title: string; description: string; button: string; variant: "warning" | "danger" | "secondary" }> = {
  suspend: {
    title: "Suspender cliente",
    description: "Todas as API Keys e acessos aos serviços ativos serão suspensos imediatamente.",
    button: "Suspender",
    variant: "warning",
  },
  reactivate: {
    title: "Reativar cliente",
    description: "O cliente voltará ao status ativo e os serviços serão reativados.",
    button: "Reativar",
    variant: "secondary",
  },
  cancel: {
    title: "Cancelar cliente",
    description: "Esta ação é irreversível. O cliente será marcado como cancelado.",
    button: "Cancelar conta",
    variant: "danger",
  },
};

export default function CustomerDetailPage({ params }: { params: { id: string } }) {
  const qc = useQueryClient();
  const [confirm, setConfirm] = useState<Action | null>(null);

  const { data: customer, isLoading, isError } = useQuery({
    queryKey: ["admin-customer", params.id],
    queryFn: () => adminService.getCustomer(params.id),
  });

  const { data: subsData } = useQuery({
    queryKey: ["admin-subscriptions-customer", params.id],
    queryFn: () => adminService.listSubscriptions({ customer_id: params.id }),
    enabled: !!customer,
    staleTime: 30_000,
  });

  const { data: invoicesData } = useQuery({
    queryKey: ["admin-invoices-customer", params.id],
    queryFn: () => adminService.listInvoices({ customer_id: params.id }),
    enabled: !!customer,
    staleTime: 30_000,
  });

  const { data: quotaData, refetch: refetchQuota } = useQuery({
    queryKey: ["admin-customer-quota", params.id],
    queryFn: () => adminService.getCustomerQuota(params.id),
    enabled: !!customer,
    staleTime: 60_000,
  });

  const actionMutation = useMutation({
    mutationFn: (action: Action) => {
      if (action === "suspend") return adminService.suspendCustomer(params.id);
      if (action === "reactivate") return adminService.reactivateCustomer(params.id);
      return adminService.cancelCustomer(params.id);
    },
    onSuccess: (_, action) => {
      qc.invalidateQueries({ queryKey: ["admin-customer", params.id] });
      qc.invalidateQueries({ queryKey: ["admin-customers"] });
      setConfirm(null);
      const labels: Record<Action, string> = { suspend: "suspenso", reactivate: "reativado", cancel: "cancelado" };
      toast.success(`Cliente ${labels[action]} com sucesso.`);
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao executar ação.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  if (isLoading) return <DetailSkeleton />;

  if (isError || !customer) {
    return (
      <div className="text-center py-20">
        <p className="text-sm text-text-secondary">Cliente não encontrado.</p>
        <Link href="/backoffice/customers" className="text-xs text-brand-accent underline mt-2 block">
          Voltar para clientes
        </Link>
      </div>
    );
  }

  const createdAt = new Date(customer.created_at).toLocaleDateString("pt-BR");
  const updatedAt = new Date(customer.updated_at).toLocaleDateString("pt-BR");
  const subs = subsData?.results ?? [];
  const invoices = invoicesData?.results ?? [];

  return (
    <div className="space-y-8 max-w-3xl">
      <Link
        href="/backoffice/customers"
        className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
        <ChevronLeft size={14} />
        Clientes
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-accent/10 flex items-center justify-center flex-shrink-0">
            <Building2 size={18} className="text-brand-accent" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">{customer.company_name}</h1>
            <p className="text-sm text-text-secondary font-mono mt-1">{customer.document}</p>
          </div>
        </div>
        <StatusBadge status={customer.status} />
      </div>

      {/* Actions */}
      <div className="flex gap-3 flex-wrap">
        {customer.status === "active" && (
          <Button size="sm" variant="warning" onClick={() => setConfirm("suspend")}>
            Suspender
          </Button>
        )}
        {customer.status === "suspended" && (
          <Button size="sm" variant="secondary" onClick={() => setConfirm("reactivate")}>
            Reativar
          </Button>
        )}
        {customer.status !== "cancelled" && (
          <Button size="sm" variant="danger" onClick={() => setConfirm("cancel")}>
            Cancelar conta
          </Button>
        )}
      </div>

      {/* Info */}
      <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
        <InfoRow label="ID" value={customer.id} mono />
        <InfoRow label="Criado em" value={createdAt} />
        <InfoRow label="Atualizado em" value={updatedAt} />
        {customer.asaas_customer_id && (
          <InfoRow label="ID Asaas" value={customer.asaas_customer_id} mono />
        )}
      </div>

      {/* Quota */}
      {quotaData && (
        <QuotaSection
          customerId={params.id}
          quota={quotaData}
          onUpdated={() => refetchQuota()}
        />
      )}

      {/* Subscriptions */}
      <section>
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
          Assinaturas ({subs.length})
        </h2>
        {subs.length === 0 ? (
          <p className="text-sm text-text-tertiary">Nenhuma assinatura.</p>
        ) : (
          <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
            {subs.map((sub) => (
              <SubscriptionRow key={sub.id} sub={sub} />
            ))}
          </div>
        )}
      </section>

      {/* Invoices */}
      <section>
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
          Faturas recentes ({invoices.length})
        </h2>
        {invoices.length === 0 ? (
          <p className="text-sm text-text-tertiary">Nenhuma fatura.</p>
        ) : (
          <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
            {invoices.map((inv) => (
              <InvoiceRow key={inv.id} invoice={inv} />
            ))}
          </div>
        )}
      </section>

      {confirm && (
        <ConfirmDialog
          customer={customer}
          action={confirm}
          loading={actionMutation.isPending}
          onConfirm={() => actionMutation.mutate(confirm)}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}

function InfoRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between px-5 py-3.5">
      <span className="text-sm text-text-secondary">{label}</span>
      <span className={`text-sm font-medium ${mono ? "font-mono text-xs text-text-tertiary" : "text-text-primary"}`}>
        {value}
      </span>
    </div>
  );
}

const CYCLE_LABEL: Record<string, string> = {
  monthly: "Mensal",
  annual: "Anual",
  one_time: "Única",
  lifetime: "Vitalício",
};

function SubscriptionRow({ sub }: { sub: Subscription }) {
  const expiresAt = new Date(sub.expires_at).toLocaleDateString("pt-BR");
  const cycle = CYCLE_LABEL[sub.billing_cycle] ?? sub.billing_cycle;

  return (
    <div className="flex items-center justify-between px-5 py-3.5">
      <div>
        <p className="text-sm font-medium text-text-primary">{sub.product_name}</p>
        <p className="text-xs text-text-tertiary mt-0.5">
          {cycle} · R$ {parseFloat(sub.amount).toFixed(2)} · vence {expiresAt}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <StatusBadge status={sub.status} />
        <Link
          href={`/backoffice/subscriptions/${sub.id}`}
          className="text-xs text-brand-accent hover:underline"
        >
          Detalhe →
        </Link>
      </div>
    </div>
  );
}

function InvoiceRow({ invoice }: { invoice: AdminInvoice }) {
  const dueDate = new Date(invoice.due_date).toLocaleDateString("pt-BR");

  return (
    <div className="flex items-center justify-between px-5 py-3.5">
      <div>
        <p className="text-sm font-medium text-text-primary">
          R$ {parseFloat(invoice.amount).toFixed(2)}
        </p>
        <p className="text-xs text-text-tertiary mt-0.5">Vence em {dueDate}</p>
      </div>
      <StatusBadge status={invoice.status} />
    </div>
  );
}

function ConfirmDialog({
  customer,
  action,
  loading,
  onConfirm,
  onCancel,
}: {
  customer: AdminCustomer;
  action: Action;
  loading: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const meta = ACTION_META[action];
  const titleId = useId();
  const descriptionId = useId();

  return (
    <Dialog onClose={onCancel} titleId={titleId} descriptionId={descriptionId} className="max-w-sm p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary">{meta.title}</h3>
        <p id={descriptionId} className="text-sm text-text-secondary mt-2">
          <span className="font-medium text-text-primary">{customer.company_name}</span>
          {" — "}
          {meta.description}
        </p>
        <div className="flex gap-3 mt-6 justify-end">
          <Button variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
            Voltar
          </Button>
          <Button variant={meta.variant} size="sm" onClick={onConfirm} disabled={loading} loading={loading}>
            {meta.button}
          </Button>
        </div>
    </Dialog>
  );
}

function QuotaSection({
  customerId,
  quota,
  onUpdated,
}: {
  customerId: string;
  quota: CustomerQuota;
  onUpdated: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(String(quota.max_api_calls ?? ""));

  const mutation = useMutation({
    mutationFn: (n: number) => adminService.updateCustomerQuota(customerId, n),
    onSuccess: () => {
      toast.success("Quota atualizada.");
      setEditing(false);
      onUpdated();
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao atualizar quota.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const usagePct =
    quota.max_api_calls && quota.max_api_calls > 0
      ? Math.min(100, Math.round((quota.used_api_calls / quota.max_api_calls) * 100))
      : 0;

  const barColor =
    usagePct >= 90 ? "bg-danger" : usagePct >= 70 ? "bg-warning" : "bg-success";

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
          Quota de API
        </h2>
        {!editing && (
          <Button variant="ghost" size="xs" onClick={() => { setValue(String(quota.max_api_calls ?? "")); setEditing(true); }}>
            <Pencil size={12} className="mr-1" /> Editar
          </Button>
        )}
      </div>

      <div className="bg-surface-1 border border-border-subtle rounded-xl p-5 space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-xs text-text-tertiary mb-1">Chamadas usadas</p>
            <p className="text-2xl font-bold text-text-primary tabular-nums">
              {quota.used_api_calls.toLocaleString("pt-BR")}
              <span className="text-sm font-normal text-text-tertiary ml-1">
                / {quota.max_api_calls != null ? quota.max_api_calls.toLocaleString("pt-BR") : "∞"}
              </span>
            </p>
          </div>
          {quota.max_api_calls != null && (
            <span className={`text-sm font-semibold ${usagePct >= 90 ? "text-danger" : usagePct >= 70 ? "text-warning" : "text-success"}`}>
              {usagePct}%
            </span>
          )}
        </div>

        {quota.max_api_calls != null && (
          <div className="h-2 bg-surface-3 rounded-full overflow-hidden">
            <div className={`h-full ${barColor} rounded-full transition-all`} style={{ width: `${usagePct}%` }} />
          </div>
        )}

        {quota.reset_at && (
          <p className="text-xs text-text-tertiary">
            Reset em {new Date(quota.reset_at).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })}
          </p>
        )}

        {editing && (
          <div className="pt-2 border-t border-border-subtle">
            <p className="text-xs text-text-secondary mb-2">Novo limite de chamadas/mês</p>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min="0"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                className="w-40"
                placeholder="ex: 50000"
              />
              <Button
                variant="primary"
                size="sm"
                loading={mutation.isPending}
                disabled={!value || isNaN(Number(value))}
                onClick={() => mutation.mutate(Number(value))}
              >
                <Check size={13} className="mr-1" /> Salvar
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setEditing(false)} disabled={mutation.isPending}>
                <X size={13} />
              </Button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-8 max-w-3xl">
      <Skeleton className="h-4 w-24" />
      <div className="flex items-start gap-3">
        <Skeleton className="h-10 w-10 rounded-xl" />
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex justify-between px-5 py-3.5">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-40" />
          </div>
        ))}
      </div>
    </div>
  );
}
