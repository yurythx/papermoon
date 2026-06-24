"use client";

import axios from "axios";
import { useState, useEffect, useId } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import Link from "next/link";
import { Plus, Search } from "lucide-react";
import { adminService, productService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { StatusBadge } from "@/components/compound/status-badge";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { CreditCard } from "lucide-react";
import type { Pricing, Product, Subscription } from "@/types";

type Action = "suspend" | "cancel" | "renew";

export default function BackofficeSubscriptionsPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [confirm, setConfirm] = useState<{ sub: Subscription; action: Action } | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  // Debounce search to avoid hammering the API on every keystroke
  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1); }, 400);
    return () => clearTimeout(t);
  }, [searchInput]);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-subscriptions", statusFilter, search, page],
    queryFn: () => adminService.listSubscriptions({
      status: statusFilter || undefined,
      search: search || undefined,
      page,
    }),
    staleTime: 30_000,
  });

  const actionMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: Action }) => {
      if (action === "suspend") return adminService.suspendSubscription(id);
      if (action === "renew") return adminService.renewSubscription(id);
      return adminService.cancelSubscription(id);
    },
    onSuccess: (_, { action }) => {
      qc.invalidateQueries({ queryKey: ["admin-subscriptions"] });
      setConfirm(null);
      const labels: Record<Action, string> = { suspend: "suspensa", cancel: "cancelada", renew: "renovada" };
      toast.success(`Assinatura ${labels[action]} com sucesso.`);
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao executar ação.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const subs = data?.results ?? [];
  const totalPages = data ? Math.ceil(data.count / 20) : 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Assinaturas"
        description="Contratos ativos — assinaturas mensais e implantações únicas"
        actions={
          <Button size="sm" variant="primary" onClick={() => setCreateOpen(true)}>
            <Plus size={14} className="mr-1.5" />
            Nova assinatura
          </Button>
        }
      />

      <div className="flex gap-3 items-center flex-wrap">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary pointer-events-none" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Buscar por cliente…"
            className="bg-surface-1 border border-border-default text-text-primary rounded-lg pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent/50 w-52"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="bg-surface-1 border border-border-default text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent/50"
        >
          <option value="">Todos os status</option>
          <option value="trial">Trial</option>
          <option value="active">Ativa</option>
          <option value="suspended">Suspensa</option>
          <option value="grace_period">Carência</option>
          <option value="expired">Expirada</option>
          <option value="cancelled">Cancelada</option>
        </select>
        {data && (
          <p className="text-sm text-text-tertiary">
            {data.count} assinatura{data.count !== 1 ? "s" : ""}
          </p>
        )}
      </div>

      <div className="bg-surface-1 border border-border-subtle rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : subs.length === 0 ? (
          <EmptyState icon={CreditCard} title="Nenhuma assinatura encontrada" description="Tente ajustar os filtros." />
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[480px]">
            <thead>
              <tr className="border-b border-border-subtle">
                <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Plano</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Cliente</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Status</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Ciclo</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Expira em</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {subs.map((sub) => (
                <SubscriptionRow
                  key={sub.id}
                  subscription={sub}
                  onAction={(action) => setConfirm({ sub, action })}
                />
              ))}
            </tbody>
          </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <span>{data?.count} total</span>
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

      {confirm && (
        <ConfirmDialog
          subscription={confirm.sub}
          action={confirm.action}
          loading={actionMutation.isPending}
          onConfirm={() => actionMutation.mutate({ id: confirm.sub.id, action: confirm.action })}
          onCancel={() => setConfirm(null)}
        />
      )}

      {createOpen && (
        <CreateSubscriptionModal
          onCreated={() => {
            qc.invalidateQueries({ queryKey: ["admin-subscriptions"] });
            setCreateOpen(false);
          }}
          onClose={() => setCreateOpen(false)}
        />
      )}
    </div>
  );
}

const CYCLE_LABEL: Record<string, string> = {
  monthly: "Mensal",
  annual: "Anual",
  one_time: "Única",
  lifetime: "Vitalício",
};

function SubscriptionRow({ subscription: sub, onAction }: { subscription: Subscription; onAction: (a: Action) => void }) {
  const expiresAt = sub.expires_at
    ? new Date(sub.expires_at).toLocaleDateString("pt-BR")
    : "—";
  const cycle = CYCLE_LABEL[sub.billing_cycle] ?? sub.billing_cycle;

  return (
    <tr className="hover:bg-surface-2 transition-colors">
      <td className="px-5 py-3.5 font-medium text-text-primary">{sub.product_name}</td>
      <td className="px-5 py-3.5">
        {sub.customer_id ? (
          <Link
            href={`/backoffice/customers/${sub.customer_id}`}
            className="text-sm text-brand-accent hover:underline"
          >
            {sub.customer_name ?? sub.customer_id}
          </Link>
        ) : (
          <span className="text-sm text-text-tertiary">—</span>
        )}
      </td>
      <td className="px-5 py-3.5">
        <StatusBadge status={sub.status} />
      </td>
      <td className="px-5 py-3.5 text-text-secondary">{cycle}</td>
      <td className="px-5 py-3.5 text-text-secondary">{expiresAt}</td>
      <td className="px-5 py-3.5">
        <div className="flex gap-2 justify-end">
          <Link
            href={`/backoffice/subscriptions/${sub.id}`}
            className="text-xs text-brand-accent hover:underline px-1"
          >
            Detalhe
          </Link>
          {(sub.status === "active" || sub.status === "trial") && (
            <Button size="sm" variant="warning" onClick={() => onAction("suspend")}>
              Suspender
            </Button>
          )}
          {sub.status === "expired" && (
            <Button size="sm" variant="secondary" onClick={() => onAction("renew")}>
              Renovar
            </Button>
          )}
          {sub.status !== "cancelled" && (
            <Button size="sm" variant="danger" onClick={() => onAction("cancel")}>
              Cancelar
            </Button>
          )}
        </div>
      </td>
    </tr>
  );
}

type ActionMeta = { title: string; desc: string; btn: string; variant: "warning" | "danger" | "secondary" };

const ACTION_META: Record<Action, ActionMeta> = {
  suspend: { title: "Suspender assinatura", desc: "O cliente perderá acesso aos serviços imediatamente.", btn: "Suspender", variant: "warning" },
  cancel: { title: "Cancelar assinatura", desc: "Ação irreversível. A assinatura será encerrada.", btn: "Cancelar", variant: "danger" },
  renew: { title: "Renovar assinatura", desc: "A assinatura será reativada com o próximo ciclo de cobrança.", btn: "Renovar", variant: "secondary" },
};

const CYCLE_LABEL_MODAL: Record<string, string> = {
  monthly: "Mensal",
  annual: "Anual",
  one_time: "Única",
  lifetime: "Vitalício",
};

function CreateSubscriptionModal({
  onCreated,
  onClose,
}: {
  onCreated: () => void;
  onClose: () => void;
}) {
  const [customerId, setCustomerId] = useState("");
  const [productId, setProductId] = useState("");
  const [pricingId, setPricingId] = useState("");

  const { data: customersData, isLoading: loadingCustomers } = useQuery({
    queryKey: ["admin-customers-modal"],
    queryFn: () => adminService.listCustomers({ status: "active", page: 1 }),
    staleTime: 60_000,
  });

  const { data: products, isLoading: loadingProducts } = useQuery({
    queryKey: ["catalog-modal"],
    queryFn: () => productService.catalog(),
    staleTime: 60_000,
  });

  const customers = customersData?.results ?? [];
  const selectedProduct: Product | undefined = products?.find((p) => p.id === productId);
  const activePricings: Pricing[] = selectedProduct?.pricings.filter((p) => p.is_active) ?? [];

  const createMutation = useMutation({
    mutationFn: () =>
      adminService.createSubscription({ customer_id: customerId, product_id: productId, pricing_id: pricingId }),
    onSuccess: () => {
      toast.success("Assinatura criada com sucesso.");
      onCreated();
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao criar assinatura.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const canSubmit = !!customerId && !!productId && !!pricingId;
  const titleId = useId();
  const descriptionId = useId();

  return (
    <Dialog onClose={onClose} titleId={titleId} descriptionId={descriptionId} className="max-w-md p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary">Nova assinatura</h3>
        <p id={descriptionId} className="text-sm text-text-secondary mt-1 mb-5">
          A assinatura será criada manualmente. Serviços mensais e implantações únicas são suportados.
        </p>

        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider block mb-1.5">
              Cliente
            </label>
            <select
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              disabled={loadingCustomers}
              className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus disabled:opacity-50"
            >
              <option value="">Selecionar cliente…</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.company_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider block mb-1.5">
              Produto
            </label>
            <select
              value={productId}
              onChange={(e) => {
                setProductId(e.target.value);
                setPricingId("");
              }}
              disabled={loadingProducts}
              className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus disabled:opacity-50"
            >
              <option value="">Selecionar produto…</option>
              {(products ?? []).filter((p) => p.is_active).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider block mb-1.5">
              Plano / Ciclo
            </label>
            <select
              value={pricingId}
              onChange={(e) => setPricingId(e.target.value)}
              disabled={!productId || activePricings.length === 0}
              className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus disabled:opacity-50"
            >
              <option value="">
                {!productId ? "Selecione um produto primeiro" : "Selecionar plano…"}
              </option>
              {activePricings.map((pr) => (
                <option key={pr.id} value={pr.id}>
                  {CYCLE_LABEL_MODAL[pr.billing_cycle] ?? pr.billing_cycle} — R${" "}
                  {parseFloat(pr.amount).toFixed(2)}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex gap-3 mt-6 justify-end">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={createMutation.isPending}>
            Fechar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => createMutation.mutate()}
            disabled={!canSubmit}
            loading={createMutation.isPending}
          >
            Criar assinatura
          </Button>
        </div>
    </Dialog>
  );
}

function ConfirmDialog({ subscription, action, loading, onConfirm, onCancel }: {
  subscription: Subscription; action: Action; loading: boolean; onConfirm: () => void; onCancel: () => void;
}) {
  const meta = ACTION_META[action];
  const titleId = useId();
  const descriptionId = useId();
  return (
    <Dialog onClose={onCancel} titleId={titleId} descriptionId={descriptionId} className="max-w-sm p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary">{meta.title}</h3>
        <p id={descriptionId} className="text-sm text-text-secondary mt-2">
          <span className="font-medium text-text-primary">{subscription.product_name}</span> — {meta.desc}
        </p>
        <div className="flex gap-3 mt-6 justify-end">
          <Button variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
            Voltar
          </Button>
          <Button variant={meta.variant} size="sm" onClick={onConfirm} disabled={loading} loading={loading}>
            {meta.btn}
          </Button>
        </div>
    </Dialog>
  );
}
