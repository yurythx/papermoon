"use client";

import { memo, useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Plus, Pencil, Check, X } from "lucide-react";
import type { Pricing, Product } from "@/types";

export type PricingFormData = {
  billing_cycle: string;
  amount: string;
  trial_days: number;
  max_api_calls: number;
  max_users: number;
  is_active: boolean;
};

const CYCLE_OPTS = [
  { value: "monthly", label: "Mensal" },
  { value: "annual", label: "Anual" },
  { value: "one_time", label: "Cobrança Única" },
  { value: "quarterly", label: "Trimestral" },
];

const CYCLE_LABEL: Record<string, string> = {
  monthly: "Mensal",
  annual: "Anual",
  yearly: "Anual",
  one_time: "Cobrança Única",
  quarterly: "Trimestral",
  lifetime: "Vitalício",
  trial: "Trial",
};

/* ── PricingRow ─────────────────────────────────────────────────────── */

interface PricingRowProps {
  pricing: Pricing;
  editing: boolean;
  saving: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave: (data: Omit<PricingFormData, "billing_cycle">) => void;
}

const PricingRow = memo(function PricingRow({ pricing, editing, saving, onEdit, onCancel, onSave }: PricingRowProps) {
  const [amount, setAmount] = useState(pricing.amount);
  const [trialDays, setTrialDays] = useState(String(pricing.trial_days));
  const [maxCalls, setMaxCalls] = useState(String(pricing.max_api_calls ?? 0));
  const [maxUsers, setMaxUsers] = useState(String(pricing.max_users ?? 0));
  const [isActive, setIsActive] = useState(pricing.is_active);

  if (!editing) {
    return (
      <div className="px-6 py-4 border-b border-border-subtle last:border-0 flex items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-text-primary">
              R$ {parseFloat(pricing.amount).toFixed(2)}
            </span>
            <Badge variant="muted">{CYCLE_LABEL[pricing.billing_cycle] ?? pricing.billing_cycle}</Badge>
            {!pricing.is_active && <Badge variant="muted">Inativo</Badge>}
            {pricing.trial_days > 0 && <Badge variant="info">{pricing.trial_days}d trial</Badge>}
          </div>
          <p className="text-xs text-text-tertiary">
            {(pricing.max_api_calls ?? 0) > 0 && `${(pricing.max_api_calls ?? 0).toLocaleString("pt-BR")} chamadas · `}
            {(pricing.max_users ?? 0) > 0 && `${pricing.max_users} usuários`}
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={onEdit}>
          <Pencil size={12} className="mr-1" />
          Editar
        </Button>
      </div>
    );
  }

  return (
    <div className="px-6 py-4 border-b border-border-subtle bg-surface-3/30 space-y-3">
      <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
        Editando — {CYCLE_LABEL[pricing.billing_cycle] ?? pricing.billing_cycle}
      </p>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-text-tertiary mb-1">Valor (R$)</label>
          <Input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="199.00" />
        </div>
        <div>
          <label className="block text-xs text-text-tertiary mb-1">Dias de trial</label>
          <Input value={trialDays} onChange={(e) => setTrialDays(e.target.value)} placeholder="0" type="number" min="0" />
        </div>
        <div>
          <label className="block text-xs text-text-tertiary mb-1">Chamadas/mês</label>
          <Input value={maxCalls} onChange={(e) => setMaxCalls(e.target.value)} placeholder="10000" type="number" min="0" />
        </div>
        <div>
          <label className="block text-xs text-text-tertiary mb-1">Usuários máx.</label>
          <Input value={maxUsers} onChange={(e) => setMaxUsers(e.target.value)} placeholder="5" type="number" min="0" />
        </div>
      </div>
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={isActive}
          onChange={(e) => setIsActive(e.target.checked)}
          className="w-4 h-4 accent-brand-accent"
        />
        <span className="text-xs text-text-secondary">Ativo</span>
      </label>
      <div className="flex gap-2 pt-1">
        <Button
          variant="primary"
          size="sm"
          loading={saving}
          onClick={() =>
            onSave({
              amount,
              trial_days: Number(trialDays),
              max_api_calls: Number(maxCalls),
              max_users: Number(maxUsers),
              is_active: isActive,
            })
          }
        >
          <Check size={12} className="mr-1" /> Salvar
        </Button>
        <Button variant="ghost" size="sm" onClick={onCancel} disabled={saving}>
          Cancelar
        </Button>
      </div>
    </div>
  );
});

/* ── PricingForm ────────────────────────────────────────────────────── */

interface PricingFormProps {
  saving: boolean;
  onSave: (data: PricingFormData) => void;
  onCancel: () => void;
}

function PricingForm({ saving, onSave, onCancel }: PricingFormProps) {
  const [cycle, setCycle] = useState("monthly");
  const [amount, setAmount] = useState("");
  const [trialDays, setTrialDays] = useState("0");
  const [maxCalls, setMaxCalls] = useState("10000");
  const [maxUsers, setMaxUsers] = useState("5");
  const [isActive, setIsActive] = useState(true);

  return (
    <div className="px-6 py-4 border-b border-border-subtle bg-surface-3/30 space-y-3">
      <p className="text-xs font-semibold text-text-secondary uppercase tracking-wide">Nova precificação</p>
      <div>
        <label className="block text-xs text-text-tertiary mb-1">Ciclo</label>
        <select
          value={cycle}
          onChange={(e) => setCycle(e.target.value)}
          className="w-full rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-border-focus"
        >
          {CYCLE_OPTS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-text-tertiary mb-1">Valor (R$) *</label>
          <Input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="199.00" />
        </div>
        <div>
          <label className="block text-xs text-text-tertiary mb-1">Dias de trial</label>
          <Input value={trialDays} onChange={(e) => setTrialDays(e.target.value)} placeholder="0" type="number" min="0" />
        </div>
        <div>
          <label className="block text-xs text-text-tertiary mb-1">Chamadas/mês</label>
          <Input value={maxCalls} onChange={(e) => setMaxCalls(e.target.value)} placeholder="10000" type="number" min="0" />
        </div>
        <div>
          <label className="block text-xs text-text-tertiary mb-1">Usuários máx.</label>
          <Input value={maxUsers} onChange={(e) => setMaxUsers(e.target.value)} placeholder="5" type="number" min="0" />
        </div>
      </div>
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={isActive}
          onChange={(e) => setIsActive(e.target.checked)}
          className="h-4 w-4 accent-brand-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-2"
        />
        <span className="text-xs text-text-secondary">Ativo</span>
      </label>
      <div className="flex gap-2 pt-1">
        <Button
          variant="primary"
          size="sm"
          loading={saving}
          disabled={!amount.trim()}
          onClick={() =>
            onSave({
              billing_cycle: cycle,
              amount,
              trial_days: Number(trialDays),
              max_api_calls: Number(maxCalls),
              max_users: Number(maxUsers),
              is_active: isActive,
            })
          }
        >
          <Check size={12} className="mr-1" /> Criar
        </Button>
        <Button variant="ghost" size="sm" onClick={onCancel} disabled={saving}>
          Cancelar
        </Button>
      </div>
    </div>
  );
}

/* ── PricingManagerModal ────────────────────────────────────────────── */

interface PricingManagerModalProps {
  product: Product;
  creating: boolean;
  updating: boolean;
  onCreatePricing: (data: PricingFormData) => void;
  onUpdatePricing: (id: string, data: Omit<PricingFormData, "billing_cycle">) => void;
  onClose: () => void;
}

export function PricingManagerModal({
  product,
  creating,
  updating,
  onCreatePricing,
  onUpdatePricing,
  onClose,
}: PricingManagerModalProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showNewForm, setShowNewForm] = useState(product.pricings.length === 0);
  const titleId = useId();
  const descriptionId = useId();

  return (
    <Dialog
      onClose={onClose}
      titleId={titleId}
      descriptionId={descriptionId}
      className="max-w-lg overflow-hidden"
    >
        <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
          <div>
            <h3 id={titleId} className="text-base font-semibold text-text-primary">Precificações</h3>
            <p id={descriptionId} className="text-xs text-text-tertiary mt-0.5">{product.name}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-text-tertiary hover:text-text-primary hover:bg-surface-3 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-2"
            aria-label="Fechar modal de precificações"
          >
            <X size={16} />
          </button>
        </div>

        <div className="max-h-[60vh] overflow-y-auto">
          {product.pricings.length === 0 && !showNewForm && (
            <p className="px-6 py-8 text-sm text-text-tertiary text-center">Nenhuma precificação cadastrada.</p>
          )}

          {product.pricings.map((p) => (
            <PricingRow
              key={p.id}
              pricing={p}
              editing={editingId === p.id}
              saving={updating}
              onEdit={() => { setEditingId(p.id); setShowNewForm(false); }}
              onCancel={() => setEditingId(null)}
              onSave={(data) => { onUpdatePricing(p.id, data); setEditingId(null); }}
            />
          ))}

          {showNewForm && (
            <PricingForm
              saving={creating}
              onSave={(data) => { onCreatePricing(data); setShowNewForm(false); }}
              onCancel={() => setShowNewForm(false)}
            />
          )}
        </div>

        <div className="px-6 py-3.5 border-t border-border-subtle flex justify-between items-center">
          <Button
            variant="secondary"
            size="sm"
            disabled={showNewForm}
            onClick={() => { setShowNewForm(true); setEditingId(null); }}
          >
            <Plus size={13} className="mr-1" />
            Nova precificação
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Fechar
          </Button>
        </div>
    </Dialog>
  );
}
