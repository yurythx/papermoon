"use client";

import { useState, useCallback, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import Link from "next/link";
import Image from "next/image";
import { adminService } from "@/lib/services";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ArrowLeft,
  Plus,
  Trash2,
  GripVertical,
  Save,
  FileEdit,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ImageIcon,
  Upload,
  X,
} from "lucide-react";
import type {
  CmsImage,
  CmsPageAdmin,
  CmsPageAdminPayload,
  CmsStep,
  CmsFAQ,
  CmsFeatureGroup,
  CmsFeatureItem,
  CmsResponsibility,
} from "@/types";

/* ── Helpers ─────────────────────────────────────────────────────── */

function newStep(order: number): CmsStep {
  return { number: String(order).padStart(2, "0"), title: "", description: "", order };
}
function newFaq(order: number): CmsFAQ {
  return { question: "", answer: "", order };
}
function newGroup(order: number): CmsFeatureGroup {
  return { title: "", order, items: [] };
}
function newItem(order: number): CmsFeatureItem {
  return { text: "", order };
}

const PAPERMOON_RESPONSIBILITY_SIDE = "papermoon" as const;

function newResp(side: CmsResponsibility["side"], order: number): CmsResponsibility {
  return { side, text: "", order };
}

/* ── Section wrapper ─────────────────────────────────────────────── */

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
    <div className="rounded-xl border border-border-subtle bg-surface-1 overflow-hidden">
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

/* ── Field primitives ────────────────────────────────────────────── */

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-text-secondary">{label}</label>
      {children}
    </div>
  );
}

function TextArea({
  value,
  onChange,
  rows = 3,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  placeholder?: string;
}) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={rows}
      placeholder={placeholder}
      className="w-full rounded-md border border-border-subtle bg-surface-0 px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-brand-accent resize-none"
    />
  );
}

/* ── Inline item row ─────────────────────────────────────────────── */

function ItemRow({
  onRemove,
  children,
}: {
  onRemove: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-2 group">
      <GripVertical size={16} className="text-text-tertiary mt-2.5 shrink-0 cursor-grab" />
      <div className="flex-1 space-y-2">{children}</div>
      <button
        type="button"
        onClick={onRemove}
        className="mt-2 text-text-tertiary hover:text-danger transition-colors shrink-0"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

/* ── Editor component ────────────────────────────────────────────── */

function CmsEditor({ slug, initial }: { slug: string; initial: CmsPageAdmin }) {
  const qc = useQueryClient();
  const heroInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);
  const [galleryDragging, setGalleryDragging] = useState(false);

  // Scalar fields
  const [tagline, setTagline] = useState(initial.tagline);
  const [description, setDescription] = useState(initial.description);
  const [heroAlt, setHeroAlt] = useState(initial.hero_image_alt);
  const [metaTitle, setMetaTitle] = useState(initial.meta_title);
  const [metaDesc, setMetaDesc] = useState(initial.meta_description);
  const [heroImageUrl, setHeroImageUrl] = useState<string | null>(initial.hero_image_url);

  // Gallery images (managed separately via individual API calls)
  const [galleryImages, setGalleryImages] = useState<CmsImage[]>(initial.images);

  // Nested collections (local copies)
  const [steps, setSteps] = useState<CmsStep[]>(initial.steps);
  const [faqs, setFaqs] = useState<CmsFAQ[]>(initial.faqs);
  const [groups, setGroups] = useState<CmsFeatureGroup[]>(initial.feature_groups);
  const [papermoonDoes, setPapermoonDoes] = useState<CmsResponsibility[]>(
    initial.responsibilities.filter((r) => r.side === PAPERMOON_RESPONSIBILITY_SIDE)
  );
  const [clientDoes, setClientDoes] = useState<CmsResponsibility[]>(
    initial.responsibilities.filter((r) => r.side === "client")
  );

  const mutation = useMutation({
    mutationFn: (payload: CmsPageAdminPayload) => adminService.updateCmsPage(slug, payload),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["admin-cms-pages"] });
      qc.setQueryData(["admin-cms-page", slug], data);
      toast.success("Página salva! ISR revalidando em segundos.");
    },
    onError: () => toast.error("Erro ao salvar a página."),
  });

  const heroUploadMutation = useMutation({
    mutationFn: (file: File) => adminService.uploadCmsHero(slug, file),
    onSuccess: (data) => {
      setHeroImageUrl(data.hero_image_url);
      qc.invalidateQueries({ queryKey: ["admin-cms-pages"] });
      toast.success("Imagem hero atualizada!");
    },
    onError: () => toast.error("Erro ao enviar imagem."),
  });

  const heroDeleteMutation = useMutation({
    mutationFn: () => adminService.deleteCmsHero(slug),
    onSuccess: () => {
      setHeroImageUrl(null);
      qc.invalidateQueries({ queryKey: ["admin-cms-pages"] });
      toast.success("Imagem hero removida.");
    },
    onError: () => toast.error("Erro ao remover imagem."),
  });

  const galleryUploadMutation = useMutation({
    mutationFn: (file: File) => adminService.uploadCmsGalleryImage(slug, file),
    onSuccess: (image) => {
      setGalleryImages((prev) => [...prev, image]);
      toast.success("Imagem adicionada à galeria!");
    },
    onError: () => toast.error("Erro ao enviar imagem."),
  });

  const galleryDeleteMutation = useMutation({
    mutationFn: (pk: number) => adminService.deleteCmsGalleryImage(slug, pk),
    onSuccess: (_, pk) => {
      setGalleryImages((prev) => prev.filter((img) => img.id !== pk));
      toast.success("Imagem removida da galeria.");
    },
    onError: () => toast.error("Erro ao remover imagem."),
  });

  const handleSave = useCallback(() => {
    const responsibilities: CmsResponsibility[] = [
      ...papermoonDoes.map((r, i) => ({
        ...r,
        side: PAPERMOON_RESPONSIBILITY_SIDE,
        order: i + 1,
      })),
      ...clientDoes.map((r, i) => ({ ...r, side: "client" as const, order: i + 1 })),
    ];
    mutation.mutate({
      tagline,
      description,
      hero_image_alt: heroAlt,
      meta_title: metaTitle,
      meta_description: metaDesc,
      steps: steps.map((s, i) => ({ ...s, order: i + 1 })),
      faqs: faqs.map((f, i) => ({ ...f, order: i + 1 })),
      feature_groups: groups.map((g, i) => ({
        ...g,
        order: i + 1,
        items: g.items.map((item, j) => ({ ...item, order: j + 1 })),
      })),
      responsibilities,
    });
  }, [tagline, description, heroAlt, metaTitle, metaDesc, steps, faqs, groups, papermoonDoes, clientDoes, mutation]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <Link
            href="/backoffice/cms"
            className="shrink-0 text-text-tertiary hover:text-text-primary transition-colors"
          >
            <ArrowLeft size={18} />
          </Link>
          <div className="min-w-0">
            <h1 className="text-lg font-bold text-text-primary truncate">{initial.product_name}</h1>
            <p className="text-xs text-text-tertiary font-mono">{slug}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <a
            href={`/servicos/${slug}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-text-tertiary hover:text-text-primary transition-colors"
          >
            <ExternalLink size={13} />
            Ver página
          </a>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={mutation.isPending}
            className="gap-1.5"
          >
            <Save size={14} />
            {mutation.isPending ? "Salvando..." : "Salvar"}
          </Button>
        </div>
      </div>

      {/* Conteúdo principal */}
      <Section title="Conteúdo principal">
        <Field label="Tagline (subtítulo colorido)">
          <Input value={tagline} onChange={(e) => setTagline(e.target.value)} placeholder="Frase de impacto em até 80 chars" />
        </Field>
        <Field label="Descrição (parágrafo hero)">
          <TextArea value={description} onChange={setDescription} rows={3} placeholder="Descrição breve do serviço..." />
        </Field>

        {/* Hero image upload */}
        <Field label="Imagem hero">
          <div className="flex items-start gap-4">
            <div className="shrink-0 w-28 h-20 rounded-lg border border-border-subtle bg-surface-0 overflow-hidden flex items-center justify-center">
              {heroImageUrl ? (
                <Image
                  src={heroImageUrl}
                  alt={heroAlt || "Hero"}
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
                ref={heroInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) heroUploadMutation.mutate(file);
                  e.target.value = "";
                }}
              />
              <Button
                type="button"
                variant="secondary"
                size="sm"
                className="gap-1.5"
                onClick={() => heroInputRef.current?.click()}
                disabled={heroUploadMutation.isPending}
              >
                <Upload size={13} />
                {heroUploadMutation.isPending ? "Enviando..." : heroImageUrl ? "Substituir" : "Enviar imagem"}
              </Button>
              {heroImageUrl && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="gap-1.5 text-danger hover:text-danger"
                  onClick={() => heroDeleteMutation.mutate()}
                  disabled={heroDeleteMutation.isPending}
                >
                  <X size={13} />
                  Remover
                </Button>
              )}
              <p className="text-[11px] text-text-tertiary">PNG, JPG ou WebP. Convertida para WebP automaticamente.</p>
            </div>
          </div>
        </Field>

        <Field label="Alt text da imagem hero">
          <Input value={heroAlt} onChange={(e) => setHeroAlt(e.target.value)} placeholder="Texto alternativo para acessibilidade" />
        </Field>
      </Section>

      {/* SEO */}
      <Section title="SEO" defaultOpen={false}>
        <Field label="Meta title (até 60 chars)">
          <Input value={metaTitle} onChange={(e) => setMetaTitle(e.target.value)} placeholder="Serviço — PaperMoon" />
        </Field>
        <Field label="Meta description (até 160 chars)">
          <TextArea value={metaDesc} onChange={setMetaDesc} rows={2} placeholder="Resumo para resultados de busca..." />
        </Field>
      </Section>

      {/* Galeria de imagens */}
      <Section title={`Galeria de imagens (${galleryImages.length})`} defaultOpen={false}>
        {/* Drag-and-drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setGalleryDragging(true); }}
          onDragLeave={() => setGalleryDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setGalleryDragging(false);
            const files = Array.from(e.dataTransfer.files).filter((f) =>
              f.type.startsWith("image/")
            );
            files.forEach((file) => galleryUploadMutation.mutate(file));
          }}
          className={`rounded-xl border-2 border-dashed p-3 transition-colors ${
            galleryDragging
              ? "border-brand-accent bg-brand-accent/5"
              : "border-border-subtle"
          }`}
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {galleryImages.map((img) => (
              <div
                key={img.id}
                className="relative group rounded-lg overflow-hidden border border-border-subtle bg-surface-0 aspect-video"
              >
                <Image
                  src={img.url}
                  alt={img.alt || "Imagem da galeria"}
                  fill
                  className="object-cover"
                  unoptimized
                />
                <button
                  type="button"
                  onClick={() => galleryDeleteMutation.mutate(img.id)}
                  disabled={galleryDeleteMutation.isPending}
                  className="absolute top-1.5 right-1.5 bg-black/60 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-danger/80"
                >
                  <X size={12} />
                </button>
                {img.caption && (
                  <div className="absolute bottom-0 inset-x-0 bg-black/50 text-white text-[10px] px-2 py-1 truncate">
                    {img.caption}
                  </div>
                )}
              </div>
            ))}

            {/* Upload slot */}
            <button
              type="button"
              onClick={() => galleryInputRef.current?.click()}
              disabled={galleryUploadMutation.isPending}
              className="aspect-video rounded-lg border-2 border-dashed border-border-subtle bg-surface-0 flex flex-col items-center justify-center gap-1.5 text-text-tertiary hover:border-brand-accent hover:text-brand-accent transition-colors"
            >
              {galleryUploadMutation.isPending ? (
                <span className="text-xs">Enviando...</span>
              ) : (
                <>
                  <Upload size={18} />
                  <span className="text-xs">Adicionar</span>
                </>
              )}
            </button>
          </div>

          {galleryDragging && (
            <p className="text-center text-xs text-brand-accent mt-3 font-medium">
              Solte as imagens aqui
            </p>
          )}
        </div>

        <input
          ref={galleryInputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files ?? []);
            files.forEach((file) => galleryUploadMutation.mutate(file));
            e.target.value = "";
          }}
        />
        <p className="text-[11px] text-text-tertiary">
          PNG, JPG ou WebP — arraste diretamente ou clique em Adicionar. Convertidas para WebP automaticamente.
        </p>
      </Section>

      {/* Passos de implantação */}
      <Section title={`Passos de implantação (${steps.length})`}>
        <div className="space-y-4">
          {steps.map((step, i) => (
            <ItemRow key={i} onRemove={() => setSteps((prev) => prev.filter((_, j) => j !== i))}>
              <div className="flex gap-2">
                <div className="w-16 shrink-0">
                  <Input
                    value={step.number}
                    onChange={(e) => setSteps((prev) => prev.map((s, j) => j === i ? { ...s, number: e.target.value } : s))}
                    placeholder="01"
                  />
                </div>
                <Input
                  value={step.title}
                  onChange={(e) => setSteps((prev) => prev.map((s, j) => j === i ? { ...s, title: e.target.value } : s))}
                  placeholder="Título do passo"
                  className="flex-1"
                />
              </div>
              <TextArea
                value={step.description}
                onChange={(v) => setSteps((prev) => prev.map((s, j) => j === i ? { ...s, description: v } : s))}
                rows={2}
                placeholder="O que acontece nesse passo..."
              />
            </ItemRow>
          ))}
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="gap-1.5 mt-2"
          onClick={() => setSteps((prev) => [...prev, newStep(prev.length + 1)])}
        >
          <Plus size={13} />
          Adicionar passo
        </Button>
      </Section>

      {/* FAQs */}
      <Section title={`Perguntas frequentes — FAQ (${faqs.length})`}>
        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <ItemRow key={i} onRemove={() => setFaqs((prev) => prev.filter((_, j) => j !== i))}>
              <Input
                value={faq.question}
                onChange={(e) => setFaqs((prev) => prev.map((f, j) => j === i ? { ...f, question: e.target.value } : f))}
                placeholder="Pergunta..."
              />
              <TextArea
                value={faq.answer}
                onChange={(v) => setFaqs((prev) => prev.map((f, j) => j === i ? { ...f, answer: v } : f))}
                rows={2}
                placeholder="Resposta..."
              />
            </ItemRow>
          ))}
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="gap-1.5 mt-2"
          onClick={() => setFaqs((prev) => [...prev, newFaq(prev.length + 1)])}
        >
          <Plus size={13} />
          Adicionar pergunta
        </Button>
      </Section>

      {/* Funcionalidades */}
      <Section title={`Grupos de funcionalidades (${groups.length})`}>
        <div className="space-y-5">
          {groups.map((group, gi) => (
            <div key={gi} className="rounded-lg border border-border-subtle bg-surface-0 p-4 space-y-3">
              <div className="flex items-center gap-2">
                <GripVertical size={15} className="text-text-tertiary shrink-0 cursor-grab" />
                <Input
                  value={group.title}
                  onChange={(e) =>
                    setGroups((prev) => prev.map((g, j) => j === gi ? { ...g, title: e.target.value } : g))
                  }
                  placeholder="Nome do grupo (ex: Comunicação)"
                  className="flex-1"
                />
                <button
                  type="button"
                  onClick={() => setGroups((prev) => prev.filter((_, j) => j !== gi))}
                  className="text-text-tertiary hover:text-danger transition-colors shrink-0"
                >
                  <Trash2 size={14} />
                </button>
              </div>

              <div className="pl-6 space-y-2">
                {group.items.map((item, ii) => (
                  <div key={ii} className="flex items-center gap-2">
                    <Input
                      value={item.text}
                      onChange={(e) =>
                        setGroups((prev) =>
                          prev.map((g, j) =>
                            j !== gi
                              ? g
                              : { ...g, items: g.items.map((it, k) => k === ii ? { ...it, text: e.target.value } : it) }
                          )
                        )
                      }
                      placeholder="Funcionalidade..."
                      className="flex-1"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setGroups((prev) =>
                          prev.map((g, j) => j !== gi ? g : { ...g, items: g.items.filter((_, k) => k !== ii) })
                        )
                      }
                      className="text-text-tertiary hover:text-danger transition-colors"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="gap-1 text-xs h-7"
                  onClick={() =>
                    setGroups((prev) =>
                      prev.map((g, j) => j !== gi ? g : { ...g, items: [...g.items, newItem(g.items.length + 1)] })
                    )
                  }
                >
                  <Plus size={11} />
                  Adicionar item
                </Button>
              </div>
            </div>
          ))}
        </div>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          className="gap-1.5 mt-2"
          onClick={() => setGroups((prev) => [...prev, newGroup(prev.length + 1)])}
        >
          <Plus size={13} />
          Adicionar grupo
        </Button>
      </Section>

      {/* Responsabilidades */}
      <Section title="O que é de quem?" defaultOpen={false}>
        <div className="grid sm:grid-cols-2 gap-5">
          <div className="space-y-2">
            <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">PaperMoon faz</p>
            {papermoonDoes.map((r, i) => (
              <div key={i} className="flex items-center gap-2">
                <Input
                  value={r.text}
                  onChange={(e) =>
                    setPapermoonDoes((prev) => prev.map((x, j) => j === i ? { ...x, text: e.target.value } : x))
                  }
                  placeholder="O que a PaperMoon entrega..."
                  className="flex-1"
                />
                <button
                  type="button"
                  onClick={() => setPapermoonDoes((prev) => prev.filter((_, j) => j !== i))}
                  className="text-text-tertiary hover:text-danger transition-colors"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="gap-1 text-xs h-7"
              onClick={() =>
                setPapermoonDoes((prev) => [
                  ...prev,
                  newResp(PAPERMOON_RESPONSIBILITY_SIDE, prev.length + 1),
                ])
              }
            >
              <Plus size={11} />
              Adicionar
            </Button>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Cliente faz</p>
            {clientDoes.map((r, i) => (
              <div key={i} className="flex items-center gap-2">
                <Input
                  value={r.text}
                  onChange={(e) =>
                    setClientDoes((prev) => prev.map((x, j) => j === i ? { ...x, text: e.target.value } : x))
                  }
                  placeholder="Responsabilidade do cliente..."
                  className="flex-1"
                />
                <button
                  type="button"
                  onClick={() => setClientDoes((prev) => prev.filter((_, j) => j !== i))}
                  className="text-text-tertiary hover:text-danger transition-colors"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="gap-1 text-xs h-7"
              onClick={() => setClientDoes((prev) => [...prev, newResp("client", prev.length + 1)])}
            >
              <Plus size={11} />
              Adicionar
            </Button>
          </div>
        </div>
      </Section>

      {/* Save button (bottom) */}
      <div className="flex justify-end pt-2">
        <Button onClick={handleSave} disabled={mutation.isPending} className="gap-1.5">
          <Save size={14} />
          {mutation.isPending ? "Salvando..." : "Salvar página"}
        </Button>
      </div>
    </div>
  );
}

/* ── Page ────────────────────────────────────────────────────────── */

export default function CmsEditorPage({ params }: { params: { slug: string } }) {
  const { slug } = params;

  const { data, isLoading, isError } = useQuery<CmsPageAdmin>({
    queryKey: ["admin-cms-page", slug],
    queryFn: () => adminService.getCmsPage(slug),
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
        <p className="text-sm font-medium text-text-secondary">Produto não encontrado.</p>
        <Link href="/backoffice/cms" className="text-xs text-brand-accent hover:underline mt-2">
          Voltar à lista
        </Link>
      </div>
    );
  }

  return <CmsEditor slug={slug} initial={data} />;
}
