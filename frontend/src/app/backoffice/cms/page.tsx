"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { adminService } from "@/lib/services";
import { PageHeader } from "@/components/compound/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle2, Circle, Clock, FileEdit } from "lucide-react";
import type { CmsPageAdminListItem } from "@/types";

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60_000);
  if (m < 2) return "agora mesmo";
  if (m < 60) return `${m} min atrás`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h atrás`;
  const d = Math.floor(h / 24);
  return `${d} dia${d !== 1 ? "s" : ""} atrás`;
}

function CmsRow({ item }: { item: CmsPageAdminListItem }) {
  return (
    <Link
      href={`/backoffice/cms/${item.slug}`}
      className="flex items-center justify-between px-5 py-4 rounded-xl border border-border-subtle bg-surface-1 hover:border-border-default hover:bg-surface-2 transition-colors group"
    >
      <div className="flex items-center gap-4 min-w-0">
        <div className="shrink-0">
          {item.has_page ? (
            <CheckCircle2 size={18} className="text-success" />
          ) : (
            <Circle size={18} className="text-text-tertiary" />
          )}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-text-primary group-hover:text-brand-accent transition-colors truncate">
            {item.product_name}
          </p>
          <p className="text-xs text-text-tertiary font-mono mt-0.5">{item.slug}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 shrink-0 ml-4">
        {item.has_page ? (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-success/10 text-success border border-success/20">
            <CheckCircle2 size={11} />
            Configurada
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-surface-3 text-text-tertiary border border-border-subtle">
            <Circle size={11} />
            Vazia
          </span>
        )}

        {item.updated_at && (
          <span className="hidden sm:flex items-center gap-1 text-xs text-text-tertiary">
            <Clock size={11} />
            {relativeTime(item.updated_at)}
          </span>
        )}

        <FileEdit
          size={15}
          className="text-text-tertiary group-hover:text-brand-accent transition-colors"
        />
      </div>
    </Link>
  );
}

export default function BackofficeCmsPage() {
  const { data: pages = [], isLoading } = useQuery<CmsPageAdminListItem[]>({
    queryKey: ["admin-cms-pages"],
    queryFn: adminService.listCmsPages,
    staleTime: 30_000,
  });

  const configured = pages.filter((p) => p.has_page).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Páginas de Serviço"
        description={
          isLoading
            ? "Carregando..."
            : `${configured} de ${pages.length} serviços com conteúdo configurado`
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-[68px] w-full rounded-xl" />
          ))}
        </div>
      ) : pages.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <FileEdit size={32} className="text-text-tertiary mb-3" />
          <p className="text-sm font-medium text-text-secondary">Nenhum produto encontrado.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {pages.map((item) => (
            <CmsRow key={item.slug} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
