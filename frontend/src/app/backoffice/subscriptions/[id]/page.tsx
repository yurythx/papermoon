"use client";

import { useId, useState } from "react";
import Link from "next/link";
import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ChevronLeft,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  RefreshCw,
  ExternalLink,
  Plus,
  Pencil,
} from "lucide-react";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { StatusBadge } from "@/components/compound/status-badge";
import { cn } from "@/lib/utils";
import type { ServiceAccess, Subscription } from "@/types";

const CYCLE_LABEL: Record<string, string> = {
  monthly: "Mensal",
  annual: "Anual",
  one_time: "Única",
  lifetime: "Vitalício",
};

const SERVICE_LABEL: Record<string, string> = {
  chatwoot: "Chatwoot",
  n8n: "n8n",
  meta_whatsapp: "WhatsApp Meta",
  glpi: "GLPI Helpdesk",
  zabbix: "Zabbix Monitoramento",
  proxmox: "Proxmox VE",
  nextcloud: "Nextcloud",
  aapanel: "AAPanel",
  evolution_api: "Evolution API",
  tailscale: "Tailscale",
};

type SAStatus = ServiceAccess["status"];

function statusIcon(status: SAStatus) {
  if (status === "active") return <CheckCircle2 size={15} className="text-success shrink-0" />;
  if (status === "provisioning") return <Clock size={15} className="text-info shrink-0" />;
  if (status === "failed") return <AlertCircle size={15} className="text-danger shrink-0" />;
  return <XCircle size={15} className="text-text-tertiary shrink-0" />;
}

function statusText(status: SAStatus): string {
  return { active: "Ativo", provisioning: "Provisionando…", suspended: "Suspenso", failed: "Falhou" }[status] ?? status;
}

function ServiceAccessRow({ sa, onReprovision, onEdit, reprovisioning }: {
  sa: ServiceAccess;
  onReprovision: (id: string) => void;
  onEdit: (sa: ServiceAccess) => void;
  reprovisioning: string | null;
}) {
  const canReprovision = sa.status === "failed" || sa.status === "provisioning";

  return (
    <div className={cn(
      "flex items-start justify-between px-5 py-4 gap-4",
      sa.status === "failed" && "bg-danger/3"
    )}>
      <div className="flex items-start gap-3 min-w-0">
        {statusIcon(sa.status)}
        <div className="min-w-0">
          <p className="text-sm font-semibold text-text-primary">
            {SERVICE_LABEL[sa.service_key] ?? sa.service_key}
          </p>
          <p className={cn(
            "text-xs mt-0.5 font-medium",
            sa.status === "active" ? "text-success" :
            sa.status === "provisioning" ? "text-info" :
            sa.status === "failed" ? "text-danger" : "text-text-tertiary"
          )}>
            {statusText(sa.status)}
          </p>
          {sa.external_id && (
            <p className="text-[11px] font-mono text-text-tertiary mt-0.5 truncate max-w-xs">
              {sa.external_id}
            </p>
          )}
          {sa.error && (
            <p className="text-xs text-danger mt-1 max-w-sm break-words">{sa.error}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {sa.service_url && sa.status === "active" && (
          <a
            href={sa.service_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-brand-accent hover:underline"
          >
            Acessar <ExternalLink size={11} />
          </a>
        )}
        <Button
          variant="ghost"
          size="xs"
          onClick={() => onEdit(sa)}
          title="Editar ID externo"
        >
          <Pencil size={11} />
        </Button>
        {canReprovision && (
          <Button
            variant="secondary"
            size="xs"
            loading={reprovisioning === sa.id}
            onClick={() => onReprovision(sa.id)}
          >
            <RefreshCw size={11} className="mr-1" />
            Reprovisionar
          </Button>
        )}
      </div>
    </div>
  );
}

const ALL_SERVICE_KEYS = Object.keys(SERVICE_LABEL);

export default function SubscriptionDetailPage({ params }: { params: { id: string } }) {
  const qc = useQueryClient();
  const [reprovisioning, setReprovisioning] = useState<string | null>(null);
  const [addServiceOpen, setAddServiceOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<ServiceAccess | null>(null);

  const { data: sub, isLoading: loadingSub, isError } = useQuery<Subscription>({
    queryKey: ["admin-subscription-detail", params.id],
    queryFn: () => adminService.getSubscription(params.id),
  });

  const { data: services = [], isLoading: loadingServices } = useQuery<ServiceAccess[]>({
    queryKey: ["admin-service-accesses", params.id],
    queryFn: () => adminService.listServiceAccesses(params.id),
    enabled: !!sub,
    staleTime: 30_000,
  });

  const editServiceMutation = useMutation({
    mutationFn: ({ id, external_id }: { id: string; external_id: string }) =>
      adminService.patchServiceAccess(id, { external_id: external_id || undefined }),
    onSuccess: (updated) => {
      qc.setQueryData<ServiceAccess[]>(["admin-service-accesses", params.id], (prev) =>
        prev?.map((sa) => (sa.id === updated.id ? updated : sa)) ?? []
      );
      setEditTarget(null);
      toast.success("Serviço atualizado.");
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao atualizar.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const addServiceMutation = useMutation({
    mutationFn: (serviceKey: string) => adminService.addServiceAccess(params.id, serviceKey),
    onSuccess: (newSa) => {
      qc.setQueryData<ServiceAccess[]>(["admin-service-accesses", params.id], (prev) =>
        [...(prev ?? []), newSa]
      );
      setAddServiceOpen(false);
      toast.success(`Serviço "${SERVICE_LABEL[newSa.service_key] ?? newSa.service_key}" adicionado.`);
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao adicionar serviço.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
  });

  const reprovisionMutation = useMutation({
    mutationFn: (id: string) => adminService.reprovisionServiceAccess(id),
    onMutate: (id) => setReprovisioning(id),
    onSuccess: (updated) => {
      qc.setQueryData<ServiceAccess[]>(["admin-service-accesses", params.id], (prev) =>
        prev?.map((sa) => (sa.id === updated.id ? updated : sa)) ?? []
      );
      toast.success("Reprovisionamento iniciado.");
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.error?.message ?? "Erro ao reprovisionar.");
      } else {
        toast.error("Erro inesperado.");
      }
    },
    onSettled: () => setReprovisioning(null),
  });

  if (loadingSub) return <DetailSkeleton />;

  if (isError || !sub) {
    return (
      <div className="text-center py-20">
        <p className="text-sm text-text-secondary">Serviço não encontrado.</p>
        <Link href="/backoffice/subscriptions" className="text-xs text-brand-accent underline mt-2 block">
          Voltar para serviços
        </Link>
      </div>
    );
  }

  const startsAt = new Date(sub.starts_at).toLocaleDateString("pt-BR");
  const expiresAt = new Date(sub.expires_at).toLocaleDateString("pt-BR");
  const failedCount = services.filter((s) => s.status === "failed").length;
  const provisioningCount = services.filter((s) => s.status === "provisioning").length;

  return (
    <div className="space-y-8 max-w-3xl">
      <Link
        href="/backoffice/subscriptions"
        className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
        <ChevronLeft size={14} />
        Assinaturas
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">{sub.product_name}</h1>
          <p className="text-sm font-mono text-text-tertiary mt-1">{sub.id}</p>
        </div>
        <StatusBadge status={sub.status} />
      </div>

      {/* Subscription info */}
      <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
        {sub.customer_id && (
          <div className="flex items-center justify-between px-5 py-3.5">
            <span className="text-sm text-text-secondary">Cliente</span>
            <Link
              href={`/backoffice/customers/${sub.customer_id}`}
              className="text-sm font-medium text-brand-accent hover:underline"
            >
              {sub.customer_name ?? sub.customer_id}
            </Link>
          </div>
        )}
        <InfoRow label="Ciclo" value={CYCLE_LABEL[sub.billing_cycle] ?? sub.billing_cycle} />
        <InfoRow label="Valor" value={`R$ ${parseFloat(sub.amount).toFixed(2)}`} />
        <InfoRow label="Início" value={startsAt} />
        <InfoRow label="Expiração" value={expiresAt} />
      </div>

      {/* Service accesses */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
            Serviços ({services.length})
          </h2>
          <div className="flex items-center gap-3">
            {(failedCount > 0 || provisioningCount > 0) && (
              <span className="text-xs text-warning font-medium">
                {failedCount > 0 && `${failedCount} com falha`}
                {failedCount > 0 && provisioningCount > 0 && " · "}
                {provisioningCount > 0 && `${provisioningCount} provisionando`}
              </span>
            )}
            <Button
              variant="secondary"
              size="xs"
              onClick={() => setAddServiceOpen(true)}
            >
              <Plus size={11} className="mr-1" />
              Adicionar
            </Button>
          </div>
        </div>

        <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
          {loadingServices ? (
            <div className="p-5 space-y-3">
              {[1, 2].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : services.length === 0 ? (
            <p className="text-sm text-text-tertiary px-5 py-4">Nenhum serviço provisionado.</p>
          ) : (
            services.map((sa) => (
              <ServiceAccessRow
                key={sa.id}
                sa={sa}
                onReprovision={(id) => reprovisionMutation.mutate(id)}
                onEdit={setEditTarget}
                reprovisioning={reprovisioning}
              />
            ))
          )}
        </div>
      </section>

      {addServiceOpen && (
        <AddServiceModal
          existingKeys={services.map((s) => s.service_key)}
          loading={addServiceMutation.isPending}
          onAdd={(key) => addServiceMutation.mutate(key)}
          onClose={() => setAddServiceOpen(false)}
        />
      )}

      {editTarget && (
        <EditServiceModal
          sa={editTarget}
          loading={editServiceMutation.isPending}
          onSave={(externalId) => editServiceMutation.mutate({ id: editTarget.id, external_id: externalId })}
          onClose={() => setEditTarget(null)}
        />
      )}
    </div>
  );
}

function EditServiceModal({
  sa,
  loading,
  onSave,
  onClose,
}: {
  sa: ServiceAccess;
  loading: boolean;
  onSave: (externalId: string) => void;
  onClose: () => void;
}) {
  const [externalId, setExternalId] = useState(sa.external_id ?? "");
  const titleId = useId();
  const descriptionId = useId();

  return (
    <Dialog onClose={onClose} titleId={titleId} descriptionId={descriptionId} className="max-w-sm p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary">
          Editar — {SERVICE_LABEL[sa.service_key] ?? sa.service_key}
        </h3>
        <p id={descriptionId} className="text-sm text-text-secondary mt-1 mb-5">
          Defina o ID externo do serviço para vincular uma instância existente.
        </p>

        <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider block mb-1.5">
          ID externo
        </label>
        <input
          type="text"
          value={externalId}
          onChange={(e) => setExternalId(e.target.value)}
          placeholder="ex: inbox-42 ou https://..."
          className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus"
        />

        <div className="flex gap-3 mt-6 justify-end">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onSave(externalId)}
            loading={loading}
          >
            Salvar
          </Button>
        </div>
    </Dialog>
  );
}

function AddServiceModal({
  existingKeys,
  loading,
  onAdd,
  onClose,
}: {
  existingKeys: string[];
  loading: boolean;
  onAdd: (key: string) => void;
  onClose: () => void;
}) {
  const available = ALL_SERVICE_KEYS.filter((k) => !existingKeys.includes(k));
  const [selected, setSelected] = useState(available[0] ?? "");
  const titleId = useId();
  const descriptionId = useId();

  if (available.length === 0) {
    return (
      <Dialog onClose={onClose} titleId={titleId} descriptionId={descriptionId} className="max-w-sm p-6">
          <h3 id={titleId} className="text-base font-semibold text-text-primary">Adicionar serviço</h3>
          <p id={descriptionId} className="text-sm text-text-secondary mt-2">Todos os serviços disponíveis já estão nesta assinatura.</p>
          <div className="flex justify-end mt-6">
            <Button variant="ghost" size="sm" onClick={onClose}>Fechar</Button>
          </div>
      </Dialog>
    );
  }

  return (
    <Dialog onClose={onClose} titleId={titleId} descriptionId={descriptionId} className="max-w-sm p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary">Adicionar serviço</h3>
        <p id={descriptionId} className="text-sm text-text-secondary mt-1 mb-4">
          O serviço será provisionado automaticamente via Outbox.
        </p>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus"
        >
          {available.map((k) => (
            <option key={k} value={k}>
              {SERVICE_LABEL[k] ?? k}
            </option>
          ))}
        </select>
        <div className="flex gap-3 mt-6 justify-end">
          <Button variant="ghost" size="sm" onClick={onClose} disabled={loading}>
            Fechar
          </Button>
          <Button variant="primary" size="sm" onClick={() => onAdd(selected)} loading={loading} disabled={!selected}>
            Adicionar
          </Button>
        </div>
    </Dialog>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between px-5 py-3.5">
      <span className="text-sm text-text-secondary">{label}</span>
      <span className="text-sm font-medium text-text-primary">{value}</span>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-8 max-w-3xl">
      <Skeleton className="h-4 w-32" />
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-80" />
      </div>
      <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex justify-between px-5 py-3.5">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>
    </div>
  );
}
