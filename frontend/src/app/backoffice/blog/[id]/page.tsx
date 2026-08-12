"use client";

import { forwardRef, useCallback, useEffect, useId, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Link from "next/link";
import Image from "next/image";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { adminService } from "@/lib/services";
import { estimateReadingTime } from "@/lib/blog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { StatusBadge } from "@/components/compound/status-badge";
import { cardClass } from "@/components/ui/card";
import {
  ArrowLeft,
  Save,
  FileEdit,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ImageIcon,
  Upload,
  X,
  Trash2,
  Bold,
  Italic,
  Link2,
  List,
} from "lucide-react";
import type { BlogPostAdmin, BlogPostAdminPayload } from "@/types";

/* ── Preview do Markdown ─────────────────────────────────────────── */
// Sem plugin de tipografia no projeto (ver termos/page.tsx) — estiliza
// cada elemento explicitamente pra combinar com o tema escuro em vez de
// depender de uma classe "prose" que não existe aqui.
const MARKDOWN_PREVIEW_COMPONENTS: Components = {
  h1: ({ children }) => <h1 className="text-xl font-bold text-text-primary mt-5 mb-2 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-lg font-bold text-text-primary mt-5 mb-2 first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="text-base font-semibold text-text-primary mt-4 mb-1.5 first:mt-0">{children}</h3>,
  p: ({ children }) => <p className="text-sm text-text-secondary leading-relaxed mb-3">{children}</p>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-brand-accent hover:underline">
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="list-disc list-outside pl-5 text-sm text-text-secondary space-y-1 mb-3">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-outside pl-5 text-sm text-text-secondary space-y-1 mb-3">{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-border-default pl-3 text-sm text-text-tertiary italic mb-3">{children}</blockquote>
  ),
  code: ({ children }) => (
    <code className="rounded bg-surface-2 px-1.5 py-0.5 text-xs font-mono text-text-primary">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="rounded-md bg-surface-2 px-3 py-2.5 text-xs font-mono text-text-primary overflow-x-auto mb-3">{children}</pre>
  ),
  strong: ({ children }) => <strong className="font-semibold text-text-primary">{children}</strong>,
  hr: () => <hr className="border-border-subtle my-4" />,
  img: ({ src, alt }) =>
    typeof src === "string" ? (
      // eslint-disable-next-line @next/next/no-img-element -- markdown-authored, dimensões desconhecidas em tempo de build (mesma razão de blog/[slug]/page.tsx)
      <img src={src} alt={alt ?? ""} className="rounded-md my-3 w-full h-auto" />
    ) : null,
  table: ({ children }) => (
    <div className="overflow-x-auto mb-3">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-border-subtle px-2 py-1.5 text-left text-xs font-semibold text-text-tertiary">{children}</th>
  ),
  td: ({ children }) => <td className="border border-border-subtle px-2 py-1.5 text-text-secondary">{children}</td>,
};

/* ── Section wrapper (mesmo padrão de backoffice/cms/[slug]) ───────── */

function Section({
  title,
  children,
  defaultOpen = true,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={cardClass({ className: "overflow-hidden p-0" })}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold text-text-primary hover:bg-surface-2 transition-colors"
      >
        {title}
        {open ? <ChevronUp size={15} className="text-text-tertiary" /> : <ChevronDown size={15} className="text-text-tertiary" />}
      </button>
      {open && <div className="px-5 pb-5 pt-1 space-y-3 border-t border-border-subtle">{children}</div>}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-text-secondary">{label}</label>
      {children}
    </div>
  );
}

const TextArea = forwardRef<
  HTMLTextAreaElement,
  {
    value: string;
    onChange: (v: string) => void;
    rows?: number;
    placeholder?: string;
    mono?: boolean;
  }
>(function TextArea({ value, onChange, rows = 3, placeholder, mono }, ref) {
  return (
    <textarea
      ref={ref}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={rows}
      placeholder={placeholder}
      className={`w-full rounded-md border border-border-subtle bg-surface-0 px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-brand-accent resize-none ${mono ? "font-mono text-xs" : ""}`}
    />
  );
});

/* ── Delete confirmation ─────────────────────────────────────────── */

function DeleteConfirmDialog({
  title,
  loading,
  onConfirm,
  onCancel,
}: {
  title: string;
  loading: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const titleId = useId();
  const descriptionId = useId();
  return (
    <Dialog onClose={onCancel} titleId={titleId} descriptionId={descriptionId} className="max-w-sm p-6">
      <h3 id={titleId} className="text-base font-semibold text-text-primary">
        Excluir post
      </h3>
      <p id={descriptionId} className="text-sm text-text-secondary mt-2">
        <span className="font-medium text-text-primary">{title}</span>
        {" — "}
        Esta ação é irreversível. O post e a capa serão apagados permanentemente.
      </p>
      <div className="flex gap-3 mt-6 justify-end">
        <Button variant="ghost" size="sm" onClick={onCancel} disabled={loading}>
          Voltar
        </Button>
        <Button variant="danger" size="sm" onClick={onConfirm} disabled={loading} loading={loading}>
          Excluir
        </Button>
      </div>
    </Dialog>
  );
}

/* ── Editor component ────────────────────────────────────────────── */

function BlogEditor({ id, initial }: { id: string; initial: BlogPostAdmin }) {
  const qc = useQueryClient();
  const router = useRouter();
  const coverInputRef = useRef<HTMLInputElement>(null);
  const bodyTextareaRef = useRef<HTMLTextAreaElement>(null);
  const bodyImageInputRef = useRef<HTMLInputElement>(null);
  // O input de arquivo rouba o foco do textarea antes do onChange disparar —
  // sem isso a posição do cursor pra inserir a imagem já teria se perdido.
  const bodyImageCursorRef = useRef(0);
  const [showPreview, setShowPreview] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const [title, setTitle] = useState(initial.title);
  const [slug, setSlug] = useState(initial.slug);
  const [excerpt, setExcerpt] = useState(initial.excerpt);
  const [body, setBody] = useState(initial.body);
  const [coverAlt, setCoverAlt] = useState(initial.cover_image_alt);
  const [metaTitle, setMetaTitle] = useState(initial.meta_title);
  const [metaDesc, setMetaDesc] = useState(initial.meta_description);
  const [coverImageUrl, setCoverImageUrl] = useState<string | null>(initial.cover_image_url);
  const [status, setStatus] = useState(initial.status);
  const [publishedAt, setPublishedAt] = useState(initial.published_at);
  const initialTagsInput = initial.tags.map((t) => t.name).join(", ");
  const [tagsInput, setTagsInput] = useState(initialTagsInput);

  // Derivado por comparação com `initial` em vez de um setDirty(true) espalhado
  // em cada onChange — se corrige sozinho depois de salvar, já que o save
  // atualiza `initial` (via qc.setQueryData) e os campos locais já batem com
  // o que acabou de ser salvo.
  const isDirty =
    title !== initial.title ||
    slug !== initial.slug ||
    excerpt !== initial.excerpt ||
    body !== initial.body ||
    coverAlt !== initial.cover_image_alt ||
    metaTitle !== initial.meta_title ||
    metaDesc !== initial.meta_description ||
    tagsInput !== initialTagsInput;

  // Cobre fechar a aba, atualizar a página ou digitar outra URL — navegação
  // dentro do app (o link "← Blog") é interceptada separadamente, já que
  // beforeunload não dispara para isso.
  useEffect(() => {
    if (!isDirty) return;
    function handleBeforeUnload(e: BeforeUnloadEvent) {
      e.preventDefault();
      e.returnValue = "";
    }
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isDirty]);

  const mutation = useMutation({
    mutationFn: (payload: BlogPostAdminPayload) => adminService.updateBlogPost(id, payload),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["admin-blog-posts"] });
      qc.setQueryData(["admin-blog-post", id], data);
      setStatus(data.status);
      setPublishedAt(data.published_at);
      // O back normaliza (trim, ordena por nome, dedup por slug) — sem
      // ressincronizar aqui, isDirty ficaria preso em "true" depois de um
      // save bem-sucedido sempre que a formatação digitada não bater 1:1
      // com o que o servidor devolveu (ordem alfabética, espaços, etc.).
      setTagsInput(data.tags.map((t) => t.name).join(", "));
      toast.success("Post salvo! ISR revalidando em segundos.");
    },
    onError: () => toast.error("Erro ao salvar o post."),
  });

  const coverUploadMutation = useMutation({
    mutationFn: (file: File) => adminService.uploadBlogCover(id, file),
    onSuccess: (data) => {
      setCoverImageUrl(data.cover_image_url);
      qc.invalidateQueries({ queryKey: ["admin-blog-posts"] });
      toast.success("Capa atualizada!");
    },
    onError: () => toast.error("Erro ao enviar imagem."),
  });

  const bodyImageUploadMutation = useMutation({
    mutationFn: (file: File) => adminService.uploadBlogBodyImage(id, file),
    onSuccess: (data) => {
      const pos = bodyImageCursorRef.current;
      const markdown = `![](${data.image_url})`;
      setBody((current) => current.slice(0, pos) + markdown + current.slice(pos));
      toast.success("Imagem inserida — preencha o alt entre os colchetes.");
      requestAnimationFrame(() => {
        const el = bodyTextareaRef.current;
        if (!el) return;
        el.focus();
        // Seleciona o "alt" vazio entre `![` e `]` pra digitar na hora.
        el.setSelectionRange(pos + 2, pos + 2);
      });
    },
    onError: () => toast.error("Erro ao enviar imagem."),
  });

  const coverDeleteMutation = useMutation({
    mutationFn: () => adminService.deleteBlogCover(id),
    onSuccess: () => {
      setCoverImageUrl(null);
      qc.invalidateQueries({ queryKey: ["admin-blog-posts"] });
      toast.success("Capa removida.");
    },
    onError: () => toast.error("Erro ao remover imagem."),
  });

  const deleteMutation = useMutation({
    mutationFn: () => adminService.deleteBlogPost(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-blog-posts"] });
      toast.success("Post excluído.");
      router.push("/backoffice/blog");
    },
    onError: () => {
      toast.error("Erro ao excluir o post.");
      setConfirmDelete(false);
    },
  });

  const handleSave = useCallback(
    (nextStatus?: "draft" | "published") => {
      mutation.mutate({
        title,
        slug,
        excerpt,
        body,
        cover_image_alt: coverAlt,
        meta_title: metaTitle,
        meta_description: metaDesc,
        tag_names: tagsInput
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        ...(nextStatus ? { status: nextStatus } : {}),
      });
    },
    [title, slug, excerpt, body, coverAlt, metaTitle, metaDesc, tagsInput, mutation]
  );

  const isPublished = status === "published";

  // Toolbar do Markdown — insere sintaxe na posição do cursor/seleção do
  // textarea. requestAnimationFrame porque o valor do DOM só reflete o
  // novo `body` depois do próximo render (setBody é assíncrono).
  const wrapSelection = useCallback(
    (before: string, after: string, placeholder: string) => {
      const el = bodyTextareaRef.current;
      if (!el) return;
      const { selectionStart: start, selectionEnd: end } = el;
      const selected = body.slice(start, end) || placeholder;
      setBody(body.slice(0, start) + before + selected + after + body.slice(end));
      requestAnimationFrame(() => {
        el.focus();
        el.setSelectionRange(start + before.length, start + before.length + selected.length);
      });
    },
    [body]
  );

  const insertLink = useCallback(() => {
    const el = bodyTextareaRef.current;
    if (!el) return;
    const { selectionStart: start, selectionEnd: end } = el;
    const selected = body.slice(start, end);
    const label = selected || "texto do link";
    setBody(`${body.slice(0, start)}[${label}](url)${body.slice(end)}`);
    requestAnimationFrame(() => {
      el.focus();
      if (selected) {
        const urlStart = start + label.length + 3; // depois de "[label]("
        el.setSelectionRange(urlStart, urlStart + 3);
      } else {
        el.setSelectionRange(start + 1, start + 1 + label.length);
      }
    });
  }, [body]);

  const applyListPrefix = useCallback(() => {
    const el = bodyTextareaRef.current;
    if (!el) return;
    const { selectionStart: start, selectionEnd: end } = el;
    const selected = body.slice(start, end) || "item da lista";
    const prefixed = selected
      .split("\n")
      .map((line) => (line.startsWith("- ") ? line : `- ${line}`))
      .join("\n");
    setBody(body.slice(0, start) + prefixed + body.slice(end));
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(start, start + prefixed.length);
    });
  }, [body]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <Link
            href="/backoffice/blog"
            onClick={(e) => {
              if (isDirty && !window.confirm("Há mudanças não salvas. Sair mesmo assim?")) {
                e.preventDefault();
              }
            }}
            className="shrink-0 text-text-tertiary hover:text-text-primary transition-colors"
          >
            <ArrowLeft size={18} />
          </Link>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-text-primary truncate">{title || "Sem título"}</h1>
              <StatusBadge status={status} />
            </div>
            <p className="text-xs text-text-tertiary font-mono">{slug}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {isPublished && (
            <a
              href={`/blog/${slug}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-text-tertiary hover:text-text-primary transition-colors"
            >
              <ExternalLink size={13} />
              Ver post
            </a>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-danger hover:text-danger"
            onClick={() => setConfirmDelete(true)}
          >
            <Trash2 size={14} />
            Excluir
          </Button>
          <Button
            variant={isPublished ? "secondary" : "primary"}
            size="sm"
            disabled={mutation.isPending}
            onClick={() => handleSave(isPublished ? "draft" : "published")}
          >
            {isPublished ? "Voltar a rascunho" : "Publicar"}
          </Button>
          <Button size="sm" onClick={() => handleSave()} disabled={mutation.isPending} className="gap-1.5">
            <Save size={14} />
            {mutation.isPending ? "Salvando..." : "Salvar"}
          </Button>
        </div>
      </div>

      {isPublished && (
        <div className={cardClass({ tone: "success", className: "px-4 py-3 text-sm text-success" })}>
          Publicado{publishedAt ? ` em ${new Date(publishedAt).toLocaleString("pt-BR")}` : ""} — visível em{" "}
          <span className="font-mono">/blog/{slug}</span>.
        </div>
      )}

      {/* Conteúdo principal */}
      <Section title="Conteúdo principal">
        <Field label="Título">
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Título do post" />
        </Field>
        <Field label="Slug">
          <Input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="url-amigavel-do-post" />
        </Field>
        <Field label="Resumo (aparece no card da listagem e como descrição pra buscadores)">
          <TextArea value={excerpt} onChange={setExcerpt} rows={3} placeholder="Resumo curto do post..." />
        </Field>
        <Field label="Tags (separadas por vírgula — cria automaticamente as que não existirem)">
          <Input
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="Zabbix, Monitoramento, Tutorial"
          />
        </Field>

        {/* Cover image upload */}
        <Field label="Imagem de capa">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-28 h-20 rounded-lg border border-border-subtle bg-surface-0 overflow-hidden flex items-center justify-center">
              {coverImageUrl ? (
                <Image
                  src={coverImageUrl}
                  alt={coverAlt || "Capa"}
                  width={112}
                  height={80}
                  className="w-full h-full object-cover"
                  unoptimized
                />
              ) : (
                <ImageIcon size={22} className="text-text-tertiary" />
              )}
            </div>

            <div className="flex flex-col gap-2">
              <input
                ref={coverInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) coverUploadMutation.mutate(file);
                  e.target.value = "";
                }}
              />
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="gap-1.5"
                onClick={() => coverInputRef.current?.click()}
                disabled={coverUploadMutation.isPending}
              >
                <Upload size={13} />
                {coverUploadMutation.isPending ? "Enviando..." : coverImageUrl ? "Substituir" : "Enviar imagem"}
              </Button>
              {coverImageUrl && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="gap-1.5 text-danger hover:text-danger"
                  onClick={() => coverDeleteMutation.mutate()}
                  disabled={coverDeleteMutation.isPending}
                >
                  <X size={13} />
                  Remover
                </Button>
              )}
              <p className="text-[11px] text-text-tertiary">PNG, JPG ou WebP. Convertida para WebP automaticamente.</p>
            </div>
          </div>
        </Field>
        <Field label="Texto alternativo da capa">
          <Input value={coverAlt} onChange={(e) => setCoverAlt(e.target.value)} placeholder="Descrição da imagem para acessibilidade" />
        </Field>
      </Section>

      {/* Corpo em Markdown */}
      <Section title="Corpo do post (Markdown)">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-text-tertiary">
            {body.trim() ? `${estimateReadingTime(body)} min de leitura estimados` : "Vazio"}
          </p>
          <Button type="button" variant="ghost" size="xs" onClick={() => setShowPreview((v) => !v)}>
            {showPreview ? "Editar" : "Pré-visualizar"}
          </Button>
        </div>
        {showPreview ? (
          <div className="rounded-md bg-surface-0 px-4 py-3 text-sm text-text-primary">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_PREVIEW_COMPONENTS}>
              {body || "*Nada para pré-visualizar ainda.*"}
            </ReactMarkdown>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-1 rounded-md bg-surface-2 p-1 w-fit">
              <Button type="button" variant="ghost" size="xs" title="Negrito" onClick={() => wrapSelection("**", "**", "texto em negrito")}>
                <Bold size={13} />
              </Button>
              <Button type="button" variant="ghost" size="xs" title="Itálico" onClick={() => wrapSelection("_", "_", "texto em itálico")}>
                <Italic size={13} />
              </Button>
              <Button type="button" variant="ghost" size="xs" title="Link" onClick={insertLink}>
                <Link2 size={13} />
              </Button>
              <Button type="button" variant="ghost" size="xs" title="Lista" onClick={applyListPrefix}>
                <List size={13} />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="xs"
                title="Imagem"
                disabled={bodyImageUploadMutation.isPending}
                onClick={() => {
                  bodyImageCursorRef.current = bodyTextareaRef.current?.selectionStart ?? body.length;
                  bodyImageInputRef.current?.click();
                }}
              >
                {bodyImageUploadMutation.isPending ? <Spinner size="xs" /> : <ImageIcon size={13} />}
              </Button>
              <input
                ref={bodyImageInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) bodyImageUploadMutation.mutate(file);
                  e.target.value = "";
                }}
              />
            </div>
            <TextArea
              ref={bodyTextareaRef}
              value={body}
              onChange={setBody}
              rows={18}
              mono
              placeholder="# Título&#10;&#10;Escreva o post em Markdown..."
            />
          </>
        )}
      </Section>

      {/* SEO */}
      <Section title="SEO" defaultOpen={false}>
        <Field label="Meta título">
          <Input value={metaTitle} onChange={(e) => setMetaTitle(e.target.value)} placeholder="Deixe em branco para usar o título do post" />
        </Field>
        <Field label="Meta descrição">
          <TextArea value={metaDesc} onChange={setMetaDesc} rows={3} placeholder="Deixe em branco para usar o resumo" />
        </Field>
      </Section>

      <div className="flex justify-end">
        <Button onClick={() => handleSave()} disabled={mutation.isPending} className="gap-1.5">
          <Save size={14} />
          {mutation.isPending ? "Salvando..." : "Salvar post"}
        </Button>
      </div>

      {confirmDelete && (
        <DeleteConfirmDialog
          title={title}
          loading={deleteMutation.isPending}
          onConfirm={() => deleteMutation.mutate()}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────────── */

export default function BlogEditorPage({ params }: { params: { id: string } }) {
  const { id } = params;

  const { data, isLoading, isError } = useQuery<BlogPostAdmin>({
    queryKey: ["admin-blog-post", id],
    queryFn: () => adminService.getBlogPost(id),
    staleTime: 60_000,
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40 w-full rounded-xl" />
        <Skeleton className="h-40 w-full rounded-xl" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <FileEdit size={32} className="text-text-tertiary mb-3" />
        <p className="text-sm font-medium text-text-secondary">Post não encontrado.</p>
        <Link href="/backoffice/blog" className="text-xs text-brand-accent hover:underline mt-2">
          Voltar à lista
        </Link>
      </div>
    );
  }

  return <BlogEditor id={id} initial={data} />;
}
