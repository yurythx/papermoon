"use client";

import { useId, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";
import { Plus, FlaskConical, Trash2, Users as UsersIcon } from "lucide-react";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { Toggle } from "@/components/ui/toggle";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { ErrorState } from "@/components/compound/error-state";
import { cardClass } from "@/components/ui/card";
import { slugify } from "@/lib/utils";
import type { AdminCustomer, FeatureFlag, FeatureFlagPayload } from "@/types";

function apiErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    return err.response?.data?.error?.message ?? fallback;
  }
  return fallback;
}

/* ── Modal de criação ────────────────────────────────────────────── */

function CreateFlagModal({
  loading,
  onSubmit,
  onCancel,
}: {
  loading: boolean;
  onSubmit: (data: FeatureFlagPayload) => void;
  onCancel: () => void;
}) {
  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const titleId = useId();

  function handleNameChange(value: string) {
    setName(value);
    setKey(slugify(value).replace(/-/g, "_"));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim() || !name.trim()) return;
    onSubmit({ key: key.trim(), name: name.trim(), description: description.trim() });
  }

  return (
    <Dialog onClose={onCancel} titleId={titleId} className="max-w-md p-6">
      <h3 id={titleId} className="text-base font-semibold text-text-primary mb-5">
        Nova feature flag
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="ff-name" className="block text-xs font-medium text-text-secondary mb-1.5">
            Nome <span className="text-danger">*</span>
          </label>
          <Input
            id="ff-name"
            placeholder="Novo widget do dashboard"
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="ff-key" className="block text-xs font-medium text-text-secondary mb-1.5">
            Chave (usada no código) <span className="text-danger">*</span>
          </label>
          <Input
            id="ff-key"
            placeholder="new_dashboard_widget"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            required
            className="font-mono"
          />
        </div>
        <div>
          <label htmlFor="ff-desc" className="block text-xs font-medium text-text-secondary mb-1.5">
            Descrição (opcional)
          </label>
          <textarea
            id="ff-desc"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Pra que serve essa flag..."
            className="w-full resize-none rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-border-focus"
          />
        </div>
        <p className="text-xs text-text-tertiary">
          Criada desligada — liga globalmente ou escolhe customers específicos depois.
        </p>
        <div className="flex gap-3 pt-2 justify-end">
          <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
            Cancelar
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="sm"
            loading={loading}
            disabled={!key.trim() || !name.trim()}
          >
            Criar flag
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

/* ── Modal de customers habilitados ─────────────────────────────────── */

function CustomersModal({ flag, onClose }: { flag: FeatureFlag; onClose: () => void }) {
  const qc = useQueryClient();
  const titleId = useId();
  const [selected, setSelected] = useState<Set<string>>(
    new Set(flag.enabled_customers.map((c) => c.id))
  );

  const { data, isLoading } = useQuery({
    queryKey: ["admin-customers-for-flags"],
    queryFn: () => adminService.listCustomers({ page: 1 }),
    staleTime: 60_000,
  });

  const saveMutation = useMutation({
    mutationFn: () => adminService.updateFeatureFlag(flag.id, { enabled_customer_ids: Array.from(selected) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-feature-flags"] });
      toast.success("Customers atualizados.");
      onClose();
    },
    onError: (err) => toast.error(apiErrorMessage(err, "Erro ao salvar.")),
  });

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const customers: AdminCustomer[] = data?.results ?? [];

  return (
    <Dialog onClose={onClose} titleId={titleId} className="max-w-md p-6">
      <h3 id={titleId} className="text-base font-semibold text-text-primary">
        Customers — {flag.name}
      </h3>
      <p className="text-xs text-text-tertiary mt-1 mb-4">
        Só é considerado se a flag não estiver ligada globalmente.
      </p>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-9 w-full" />
          ))}
        </div>
      ) : customers.length === 0 ? (
        <p className="text-sm text-text-tertiary py-4 text-center">Nenhum customer cadastrado.</p>
      ) : (
        <div className="max-h-72 overflow-y-auto space-y-1 -mx-2 px-2">
          {customers.map((c) => (
            <label
              key={c.id}
              className="flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-surface-2 cursor-pointer transition-colors"
            >
              <input
                type="checkbox"
                checked={selected.has(c.id)}
                onChange={() => toggle(c.id)}
                className="rounded border-border-default"
              />
              <span className="text-sm text-text-primary">{c.company_name}</span>
            </label>
          ))}
        </div>
      )}

      <div className="flex gap-3 pt-5 justify-end">
        <Button variant="ghost" size="sm" onClick={onClose} disabled={saveMutation.isPending}>
          Cancelar
        </Button>
        <Button
          variant="primary"
          size="sm"
          loading={saveMutation.isPending}
          onClick={() => saveMutation.mutate()}
        >
          Salvar
        </Button>
      </div>
    </Dialog>
  );
}

/* ── Página ──────────────────────────────────────────────────────── */

export default function FeatureFlagsPage() {
  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [customersModalFlag, setCustomersModalFlag] = useState<FeatureFlag | null>(null);

  const { data: flags, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-feature-flags"],
    queryFn: () => adminService.listFeatureFlags(),
    staleTime: 30_000,
  });

  const createMutation = useMutation({
    mutationFn: (payload: FeatureFlagPayload) => adminService.createFeatureFlag(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-feature-flags"] });
      setCreateOpen(false);
      toast.success("Flag criada.");
    },
    onError: (err) => toast.error(apiErrorMessage(err, "Erro ao criar flag.")),
  });

  const toggleGlobalMutation = useMutation({
    mutationFn: ({ id, enabled_globally }: { id: number; enabled_globally: boolean }) =>
      adminService.updateFeatureFlag(id, { enabled_globally }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-feature-flags"] }),
    onError: (err) => toast.error(apiErrorMessage(err, "Erro ao atualizar flag.")),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => adminService.deleteFeatureFlag(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-feature-flags"] });
      toast.success("Flag removida.");
    },
    onError: (err) => toast.error(apiErrorMessage(err, "Erro ao remover flag.")),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Feature Flags"
        description="Liga funcionalidades globalmente ou só pra customers específicos (beta fechado, rollout manual)"
        actions={
          <Button size="sm" variant="primary" onClick={() => setCreateOpen(true)}>
            <Plus size={14} className="mr-1.5" />
            Nova flag
          </Button>
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-2xl" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState title="Não foi possível carregar as flags" onRetry={() => refetch()} />
      ) : !flags || flags.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="Nenhuma feature flag cadastrada"
          description="Crie a primeira pra fazer um rollout controlado ou beta fechado."
          action={{ label: "Nova flag", onClick: () => setCreateOpen(true), variant: "primary" }}
        />
      ) : (
        <div className="space-y-3">
          {flags.map((flag) => (
            <div key={flag.id} className={cardClass({ className: "flex items-center justify-between gap-4" })}>
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-semibold text-text-primary">{flag.name}</p>
                  <code className="text-[11px] text-text-tertiary font-mono">{flag.key}</code>
                </div>
                {flag.description && (
                  <p className="text-xs text-text-secondary mt-0.5">{flag.description}</p>
                )}
                {!flag.enabled_globally && (
                  <button
                    type="button"
                    onClick={() => setCustomersModalFlag(flag)}
                    className="mt-2 inline-flex items-center gap-1.5 text-xs text-text-tertiary hover:text-text-primary transition-colors"
                  >
                    <UsersIcon size={12} />
                    {flag.enabled_customers.length === 0
                      ? "Nenhum customer — clique pra escolher"
                      : `${flag.enabled_customers.length} customer${flag.enabled_customers.length !== 1 ? "s" : ""}`}
                  </button>
                )}
              </div>
              <div className="flex items-center gap-4 shrink-0">
                <label className="flex items-center gap-2 text-xs text-text-tertiary">
                  Global
                  <Toggle
                    checked={flag.enabled_globally}
                    onChange={(v) => toggleGlobalMutation.mutate({ id: flag.id, enabled_globally: v })}
                    disabled={toggleGlobalMutation.isPending}
                  />
                </label>
                <Button
                  variant="ghost"
                  size="xs"
                  className="text-danger hover:text-danger"
                  onClick={() => {
                    if (window.confirm(`Excluir a flag "${flag.name}"? Essa ação é irreversível.`)) {
                      deleteMutation.mutate(flag.id);
                    }
                  }}
                >
                  <Trash2 size={13} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {createOpen && (
        <CreateFlagModal
          loading={createMutation.isPending}
          onSubmit={(payload) => createMutation.mutate(payload)}
          onCancel={() => setCreateOpen(false)}
        />
      )}
      {customersModalFlag && (
        <CustomersModal flag={customersModalFlag} onClose={() => setCustomersModalFlag(null)} />
      )}
    </div>
  );
}
