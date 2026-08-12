"use client";

import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export type BlogPostCreateData = {
  title: string;
  slug: string;
  excerpt: string;
  body: string;
};

interface BlogPostFormModalProps {
  loading: boolean;
  onSubmit: (data: BlogPostCreateData) => void;
  onCancel: () => void;
}

// Mesma lógica de slugifyClientId em backoffice/integrations/keycloak/page.tsx —
// RegExp construída com \u escape (não literal colado no arquivo) por
// segurança de encoding entre editores/terminais.
const COMBINING_DIACRITICS_RE = new RegExp("[\\u0300-\\u036f]", "g");

function autoSlug(value: string): string {
  return value
    .normalize("NFD")
    .replace(COMBINING_DIACRITICS_RE, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function BlogPostFormModal({ loading, onSubmit, onCancel }: BlogPostFormModalProps) {
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [excerpt, setExcerpt] = useState("");
  const titleId = useId();

  function handleTitleChange(value: string) {
    setTitle(value);
    setSlug(autoSlug(value));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !slug.trim() || !excerpt.trim()) return;
    onSubmit({ title: title.trim(), slug: slug.trim(), excerpt: excerpt.trim(), body: "" });
  }

  return (
    <Dialog onClose={onCancel} titleId={titleId} className="max-w-md p-6">
      <h3 id={titleId} className="text-base font-semibold text-text-primary mb-5">
        Novo post
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="bp-title" className="block text-xs font-medium text-text-secondary mb-1.5">
            Título <span className="text-danger">*</span>
          </label>
          <Input
            id="bp-title"
            placeholder="Como configurar SSO com Keycloak"
            value={title}
            onChange={(e) => handleTitleChange(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="bp-slug" className="block text-xs font-medium text-text-secondary mb-1.5">
            Slug <span className="text-danger">*</span>
          </label>
          <Input
            id="bp-slug"
            placeholder="como-configurar-sso-com-keycloak"
            value={slug}
            onChange={(e) => setSlug(autoSlug(e.target.value))}
            required
          />
        </div>
        <div>
          <label htmlFor="bp-excerpt" className="block text-xs font-medium text-text-secondary mb-1.5">
            Resumo <span className="text-danger">*</span>
          </label>
          <textarea
            id="bp-excerpt"
            rows={3}
            placeholder="Aparece no card da listagem e como descrição pra buscadores..."
            value={excerpt}
            onChange={(e) => setExcerpt(e.target.value)}
            maxLength={300}
            className="w-full resize-none rounded-lg border border-border-default bg-surface-1 px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-border-focus"
          />
        </div>
        <p className="text-xs text-text-tertiary">
          Cria como rascunho — o corpo do post, capa e publicação ficam na tela seguinte.
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
            disabled={!title.trim() || !slug.trim() || !excerpt.trim()}
          >
            Criar post
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
