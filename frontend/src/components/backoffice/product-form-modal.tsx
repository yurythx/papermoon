"use client";

import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { Product } from "@/types";

export type ProductFormData = {
  name: string;
  slug: string;
  description: string;
  is_active: boolean;
};

interface ProductFormModalProps {
  initial?: Product;
  loading: boolean;
  onSubmit: (data: ProductFormData) => void;
  onCancel: () => void;
}

function autoSlug(value: string): string {
  return value.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

export function ProductFormModal({ initial, loading, onSubmit, onCancel }: ProductFormModalProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const titleId = useId();

  function handleNameChange(value: string) {
    setName(value);
    if (!initial) setSlug(autoSlug(value));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !slug.trim()) return;
    onSubmit({ name: name.trim(), slug: slug.trim(), description: description.trim(), is_active: isActive });
  }

  return (
    <Dialog onClose={onCancel} titleId={titleId} className="max-w-md p-6">
        <h3 id={titleId} className="text-base font-semibold text-text-primary mb-5">
          {initial ? "Editar produto" : "Novo produto"}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="pf-name" className="block text-xs font-medium text-text-secondary mb-1.5">
              Nome <span className="text-danger">*</span>
            </label>
            <Input
              id="pf-name"
              placeholder="Plano Pro"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="pf-slug" className="block text-xs font-medium text-text-secondary mb-1.5">
              Slug <span className="text-danger">*</span>
            </label>
            <Input
              id="pf-slug"
              placeholder="plano-pro"
              value={slug}
              onChange={(e) => setSlug(autoSlug(e.target.value))}
              required
            />
          </div>
          <div>
            <label htmlFor="pf-desc" className="block text-xs font-medium text-text-secondary mb-1.5">
              Descrição
            </label>
            <textarea
              id="pf-desc"
              rows={3}
              placeholder="Descrição do produto..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full resize-none rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-border-focus"
            />
          </div>
          <label className="flex items-center gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 accent-brand-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-2"
            />
            <span className="text-sm text-text-secondary">Produto ativo (visível no catálogo)</span>
          </label>
          <div className="flex gap-3 pt-2 justify-end">
            <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={loading}
              disabled={!name.trim() || !slug.trim()}
            >
              {initial ? "Salvar" : "Criar produto"}
            </Button>
          </div>
        </form>
    </Dialog>
  );
}
