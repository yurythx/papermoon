"use client";

import axios from "axios";
import { useState, useCallback, useId } from "react";
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
import Link from "next/link";
import { Users, Plus, Download, ShieldOff, XCircle, Clock, CheckCircle2 } from "lucide-react";
import type { AdminCustomer, PendingRegistration } from "@/types";

type Action = "suspend" | "reactivate" | "cancel" | "delete";

function exportToCsv(customers: AdminCustomer[]) {
  const rows = [
    ["ID", "Razão Social", "CNPJ", "Status", "Criado em"],
    ...customers.map((c) => [
      c.id,
      c.company_name,
      c.document,
      c.status,
      new Date(c.created_at).toLocaleDateString("pt-BR"),
    ]),
  ];
  const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "clientes.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export default function BackofficeCustomersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [confirm, setConfirm] = useState<{ customer: AdminCustomer; action: Action } | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkLoading, setBulkLoading] = useState(false);
  const [provisionTarget, setProvisionTarget] = useState<PendingRegistration | null>(null);

  const { data: pendingRegistrations = [], isLoading: pendingLoading } = useQuery({
    queryKey: ["pending-registrations"],
    queryFn: adminService.listPendingRegistrations,
    staleTime: 30_000,
  });

  const provisionMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: { company_name: string; document: string } }) =>
      adminService.provisionUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pending-registrations"] });
      queryClient.invalidateQueries({ queryKey: ["admin-customers"] });
      setProvisionTarget(null);
      toast.success("Usuário provisionado com sucesso.");
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao provisionar usuário.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const queryKey = ["admin-customers", search, statusFilter, page];

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      adminService.listCustomers({
        search: search || undefined,
        status: statusFilter || undefined,
        page,
      }),
    staleTime: 30_000,
  });

  const customers = data?.results ?? [];
  const totalPages = data ? Math.ceil(data.count / 20) : 1;

  // Selection helpers
  const allPageIds = customers.map((c) => c.id);
  const allSelected = allPageIds.length > 0 && allPageIds.every((id) => selectedIds.has(id));
  const someSelected = allPageIds.some((id) => selectedIds.has(id));

  const toggleAll = useCallback(() => {
    setSelectedIds((prev) => {
      if (allSelected) {
        const next = new Set(prev);
        allPageIds.forEach((id) => next.delete(id));
        return next;
      }
      const next = new Set(prev);
      allPageIds.forEach((id) => next.add(id));
      return next;
    });
  }, [allSelected, allPageIds]);

  const toggleOne = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const selectedCustomers = customers.filter((c) => selectedIds.has(c.id));

  const createMutation = useMutation({
    mutationFn: adminService.createCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-customers"] });
      setShowCreate(false);
      toast.success("Cliente criado com sucesso.");
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao criar cliente.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const actionMutation = useMutation<unknown, Error, { id: string; action: Action }>({
    mutationFn: ({ id, action }) => {
      if (action === "suspend") return adminService.suspendCustomer(id);
      if (action === "reactivate") return adminService.reactivateCustomer(id);
      if (action === "delete") return adminService.softDeleteCustomer(id);
      return adminService.cancelCustomer(id);
    },
    onSuccess: (_, { action }) => {
      queryClient.invalidateQueries({ queryKey: ["admin-customers"] });
      setConfirm(null);
      const labels: Record<Action, string> = {
        suspend: "suspenso",
        reactivate: "reativado",
        cancel: "cancelado",
        delete: "removido",
      };
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

  async function bulkSuspend() {
    const targets = selectedCustomers.filter((c) => c.status === "active");
    if (!targets.length) { toast.error("Nenhum cliente ativo selecionado."); return; }
    setBulkLoading(true);
    const results = await Promise.allSettled(targets.map((c) => adminService.suspendCustomer(c.id)));
    const ok = results.filter((r) => r.status === "fulfilled").length;
    const fail = results.filter((r) => r.status === "rejected").length;
    queryClient.invalidateQueries({ queryKey: ["admin-customers"] });
    setSelectedIds(new Set());
    setBulkLoading(false);
    if (ok) toast.success(`${ok} cliente(s) suspenso(s).`);
    if (fail) toast.error(`${fail} cliente(s) falharam.`);
  }

  async function bulkCancel() {
    const targets = selectedCustomers.filter((c) => c.status !== "cancelled");
    if (!targets.length) { toast.error("Nenhum cliente elegível selecionado."); return; }
    setBulkLoading(true);
    const results = await Promise.allSettled(targets.map((c) => adminService.cancelCustomer(c.id)));
    const ok = results.filter((r) => r.status === "fulfilled").length;
    const fail = results.filter((r) => r.status === "rejected").length;
    queryClient.invalidateQueries({ queryKey: ["admin-customers"] });
    setSelectedIds(new Set());
    setBulkLoading(false);
    if (ok) toast.success(`${ok} cliente(s) cancelado(s).`);
    if (fail) toast.error(`${fail} cliente(s) falharam.`);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <PageHeader title="Clientes" description="Gerencie tenants da plataforma" />
        <Button variant="primary" size="sm" onClick={() => setShowCreate(true)}>
          <Plus size={14} className="mr-1.5" />
          Novo cliente
        </Button>
      </div>

      {/* Pending registrations banner */}
      {(pendingLoading || pendingRegistrations.length > 0) && (
        <div className="bg-warning-muted border border-warning/25 rounded-xl overflow-hidden">
          <div className="px-4 py-3 flex items-center gap-2 border-b border-warning/15">
            <Clock size={14} className="text-warning shrink-0" />
            <span className="text-sm font-semibold text-warning">
              {pendingLoading ? "Carregando cadastros pendentes…" : `${pendingRegistrations.length} cadastro${pendingRegistrations.length !== 1 ? "s" : ""} aguardando provisionamento`}
            </span>
          </div>
          {!pendingLoading && (
            <div className="divide-y divide-warning/10">
              {pendingRegistrations.map((reg) => (
                <div key={reg.id} className="px-4 py-3 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary truncate">
                      {reg.name || reg.email}
                    </p>
                    <p className="text-xs text-text-tertiary truncate">
                      {reg.email}
                      {reg.company_name ? ` · ${reg.company_name}` : ""}
                      {reg.phone ? ` · ${reg.phone}` : ""}
                    </p>
                  </div>
                  <p className="text-xs text-text-tertiary shrink-0">
                    {new Date(reg.registered_at).toLocaleDateString("pt-BR")}
                  </p>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setProvisionTarget(reg)}
                  >
                    <CheckCircle2 size={13} className="mr-1.5" />
                    Provisionar
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex gap-3">
        <Input
          type="text"
          placeholder="Buscar por razão social ou CNPJ…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1"
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="bg-surface-1 border border-border-default text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-accent/50"
        >
          <option value="">Todos os status</option>
          <option value="active">Ativo</option>
          <option value="suspended">Suspenso</option>
          <option value="cancelled">Cancelado</option>
        </select>
      </div>

      {/* Bulk action bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 px-4 py-3 bg-brand-accent/10 border border-brand-accent/30 rounded-xl text-sm">
          <span className="font-medium text-text-primary mr-1">
            {selectedIds.size} selecionado{selectedIds.size !== 1 ? "s" : ""}
          </span>
          <Button
            variant="warning"
            size="xs"
            disabled={bulkLoading || selectedCustomers.every((c) => c.status !== "active")}
            onClick={bulkSuspend}
          >
            <ShieldOff size={13} className="mr-1" />
            Suspender
          </Button>
          <BulkCancelButton
            selectedCustomers={selectedCustomers}
            loading={bulkLoading}
            onConfirmed={bulkCancel}
          />
          <Button
            variant="secondary"
            size="xs"
            disabled={bulkLoading}
            onClick={() => exportToCsv(selectedCustomers)}
          >
            <Download size={13} className="mr-1" />
            Exportar CSV
          </Button>
          <button
            className="ml-auto text-xs text-text-tertiary hover:text-text-secondary"
            onClick={() => setSelectedIds(new Set())}
          >
            Limpar seleção
          </button>
        </div>
      )}

      <div className="bg-surface-1 border border-border-subtle rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : customers.length === 0 ? (
          <EmptyState
            icon={Users}
            title="Nenhum cliente encontrado"
            description="Tente ajustar os filtros de busca."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="px-4 py-3 w-10">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={(el) => { if (el) el.indeterminate = someSelected && !allSelected; }}
                      onChange={toggleAll}
                      className="rounded border-border-default accent-brand-accent cursor-pointer"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Razão social</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">CNPJ</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-text-tertiary uppercase tracking-wider">Criado em</th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {customers.map((c) => (
                  <CustomerRow
                    key={c.id}
                    customer={c}
                    selected={selectedIds.has(c.id)}
                    onToggle={() => toggleOne(c.id)}
                    onAction={(action) => setConfirm({ customer: c, action })}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <span>{data?.count} cliente{data?.count !== 1 ? "s" : ""}</span>
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
          customer={confirm.customer}
          action={confirm.action}
          loading={actionMutation.isPending}
          onConfirm={() => actionMutation.mutate({ id: confirm.customer.id, action: confirm.action })}
          onCancel={() => setConfirm(null)}
        />
      )}

      {showCreate && (
        <CreateCustomerModal
          loading={createMutation.isPending}
          onSubmit={(data) => createMutation.mutate(data)}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {provisionTarget && (
        <ProvisionModal
          registration={provisionTarget}
          loading={provisionMutation.isPending}
          onSubmit={(data) => provisionMutation.mutate({ userId: provisionTarget.id, data })}
          onCancel={() => setProvisionTarget(null)}
        />
      )}
    </div>
  );
}

// Separate component to hold the bulk-cancel confirm state locally
function BulkCancelButton({
  selectedCustomers,
  loading,
  onConfirmed,
}: {
  selectedCustomers: AdminCustomer[];
  loading: boolean;
  onConfirmed: () => Promise<void>;
}) {
  const [confirming, setConfirming] = useState(false);
  const eligible = selectedCustomers.filter((c) => c.status !== "cancelled");

  if (confirming) {
    return (
      <span className="flex items-center gap-1.5">
        <span className="text-xs text-text-secondary">Cancelar {eligible.length} cliente(s)?</span>
        <Button
          variant="danger"
          size="xs"
          disabled={loading}
          onClick={async () => { await onConfirmed(); setConfirming(false); }}
        >
          Confirmar
        </Button>
        <Button variant="ghost" size="xs" onClick={() => setConfirming(false)}>
          Não
        </Button>
      </span>
    );
  }

  return (
    <Button
      variant="danger"
      size="xs"
      disabled={loading || eligible.length === 0}
      onClick={() => setConfirming(true)}
    >
      <XCircle size={13} className="mr-1" />
      Cancelar
    </Button>
  );
}

function CustomerRow({
  customer,
  selected,
  onToggle,
  onAction,
}: {
  customer: AdminCustomer;
  selected: boolean;
  onToggle: () => void;
  onAction: (action: Action) => void;
}) {
  const createdAt = new Date(customer.created_at).toLocaleDateString("pt-BR");

  return (
    <tr className={`hover:bg-surface-2 transition-colors ${selected ? "bg-brand-accent/5" : ""}`}>
      <td className="px-4 py-3.5">
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggle}
          className="rounded border-border-default accent-brand-accent cursor-pointer"
        />
      </td>
      <td className="px-6 py-3.5 font-medium text-text-primary">
        <Link href={`/backoffice/customers/${customer.id}`} className="hover:text-brand-accent transition-colors">
          {customer.company_name}
        </Link>
      </td>
      <td className="px-6 py-3.5 text-text-secondary font-mono text-xs">{customer.document}</td>
      <td className="px-6 py-3.5">
        <StatusBadge status={customer.status} />
      </td>
      <td className="px-6 py-3.5 text-text-secondary">{createdAt}</td>
      <td className="px-6 py-3.5">
        <div className="flex gap-2 justify-end">
          {customer.status === "active" && (
            <Button size="sm" variant="warning" onClick={() => onAction("suspend")}>
              Suspender
            </Button>
          )}
          {customer.status === "suspended" && (
            <Button size="sm" variant="secondary" onClick={() => onAction("reactivate")}>
              Reativar
            </Button>
          )}
          {customer.status !== "cancelled" && (
            <Button size="sm" variant="danger" onClick={() => onAction("cancel")}>
              Cancelar
            </Button>
          )}
          {customer.status === "cancelled" && (
            <Button size="sm" variant="ghost" onClick={() => onAction("delete")}>
              Remover
            </Button>
          )}
        </div>
      </td>
    </tr>
  );
}

type ActionMeta = { title: string; description: string; button: string; variant: "warning" | "danger" | "secondary" | "ghost" };

const ACTION_META: Record<Action, ActionMeta> = {
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
  delete: {
    title: "Remover cliente",
    description: "O registro será ocultado da plataforma (soft-delete). Pode ser recuperado via banco de dados.",
    button: "Remover",
    variant: "ghost",
  },
};

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

function ProvisionModal({
  registration,
  loading,
  onSubmit,
  onCancel,
}: {
  registration: PendingRegistration;
  loading: boolean;
  onSubmit: (data: { company_name: string; document: string }) => void;
  onCancel: () => void;
}) {
  const [companyName, setCompanyName] = useState(registration.company_name);
  const [document, setDocument] = useState("");
  const titleId = useId();
  const descriptionId = useId();

  function maskCnpj(raw: string): string {
    const digits = raw.replace(/\D/g, "").slice(0, 14);
    return digits
      .replace(/^(\d{2})(\d)/, "$1.$2")
      .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1/$2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!companyName.trim() || !document.trim()) return;
    onSubmit({ company_name: companyName.trim(), document: document.trim() });
  }

  return (
    <Dialog onClose={onCancel} titleId={titleId} descriptionId={descriptionId} className="max-w-md p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary mb-1">Provisionar usuário</h3>
        <p id={descriptionId} className="text-xs text-text-tertiary mb-5">
          {registration.email}
          {registration.phone ? ` · ${registration.phone}` : ""}
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="prov-name" className="block text-xs font-medium text-text-secondary mb-1.5">
              Razão social <span className="text-danger">*</span>
            </label>
            <Input
              id="prov-name"
              placeholder="Acme Ltda"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="prov-doc" className="block text-xs font-medium text-text-secondary mb-1.5">
              CNPJ <span className="text-danger">*</span>
            </label>
            <Input
              id="prov-doc"
              placeholder="00.000.000/0000-00"
              value={document}
              onChange={(e) => setDocument(maskCnpj(e.target.value))}
              maxLength={18}
              required
            />
          </div>
          <div className="flex gap-3 pt-2 justify-end">
            <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" size="sm" loading={loading} disabled={!companyName.trim() || !document.trim()}>
              Criar empresa e vincular
            </Button>
          </div>
        </form>
    </Dialog>
  );
}

function CreateCustomerModal({
  loading,
  onSubmit,
  onCancel,
}: {
  loading: boolean;
  onSubmit: (data: { company_name: string; document: string }) => void;
  onCancel: () => void;
}) {
  const [companyName, setCompanyName] = useState("");
  const [document, setDocument] = useState("");
  const titleId = useId();

  function maskCnpj(raw: string): string {
    const digits = raw.replace(/\D/g, "").slice(0, 14);
    return digits
      .replace(/^(\d{2})(\d)/, "$1.$2")
      .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1/$2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!companyName.trim() || !document.trim()) return;
    onSubmit({ company_name: companyName.trim(), document: document.trim() });
  }

  return (
    <Dialog onClose={onCancel} titleId={titleId} className="max-w-md p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary mb-5">Novo cliente</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="cc-name" className="block text-xs font-medium text-text-secondary mb-1.5">
              Razão social <span className="text-danger">*</span>
            </label>
            <Input
              id="cc-name"
              placeholder="Acme Ltda"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="cc-doc" className="block text-xs font-medium text-text-secondary mb-1.5">
              CNPJ <span className="text-danger">*</span>
            </label>
            <Input
              id="cc-doc"
              placeholder="00.000.000/0000-00"
              value={document}
              onChange={(e) => setDocument(maskCnpj(e.target.value))}
              maxLength={18}
              required
            />
          </div>
          <div className="flex gap-3 pt-2 justify-end">
            <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" size="sm" loading={loading} disabled={!companyName.trim() || !document.trim()}>
              Criar cliente
            </Button>
          </div>
        </form>
    </Dialog>
  );
}
