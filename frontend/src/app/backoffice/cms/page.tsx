"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { toast } from "sonner";
import { adminService } from "@/lib/services";
import { PageHeader } from "@/components/compound/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cardClass } from "@/components/ui/card";
import { CheckCircle2, Circle, Clock, FileEdit } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CmsPageAdminListItem, Product } from "@/types";

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

function CmsRow({
  item,
  toggling,
  onToggle,
}: {
  item: CmsPageAdminListItem;
  toggling: boolean;
  onToggle: (isActive: boolean) => void;
}) {
  return (
    <Link
      href={`/backoffice/cms/${item.slug}`}
      className={cardClass({
        interactive: true,
        className: cn("flex items-center justify-between px-5 py-4 group", !item.is_active && "opacity-60"),
      })}
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
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-text-primary group-hover:text-brand-accent transition-colors truncate">
              {item.product_name}
            </p>
            {!item.is_active && <Badge variant="muted">Indisponível</Badge>}
          </div>
          <p className="text-xs text-text-tertiary font-mono mt-0.5">{item.slug}</p>
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0 ml-4">
        {item.has_page ? (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-success/10 text-success">
            <CheckCircle2 size={11} />
            Configurada
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-surface-3 text-text-tertiary">
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

        {/* Disponibilidade pública — mesmo Product.is_active da página Produtos.
            preventDefault/stopPropagation pra não navegar pro editor ao clicar. */}
        <Button
          variant={item.is_active ? "ghost" : "secondary"}
          size="sm"
          disabled={toggling}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onToggle(!item.is_active);
          }}
        >
          {item.is_active ? "Desativar" : "Ativar"}
        </Button>

        <FileEdit
          size={15}
          className="text-text-tertiary group-hover:text-brand-accent transition-colors"
        />
      </div>
    </Link>
  );
}

export default function BackofficeCmsPage() {
  const queryClient = useQueryClient();

  const { data: pages = [], isLoading } = useQuery<CmsPageAdminListItem[]>({
    queryKey: ["admin-cms-pages"],
    queryFn: adminService.listCmsPages,
    staleTime: 30_000,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      adminService.toggleProduct(id, isActive),
    onSuccess: (updated: Product) => {
      queryClient.setQueryData<CmsPageAdminListItem[]>(["admin-cms-pages"], (prev) =>
        prev?.map((p) =>
          p.product_id === updated.id ? { ...p, is_active: updated.is_active } : p
        ) ?? []
      );
      toast.success(
        updated.is_active
          ? "Serviço disponível novamente — volta a aparecer no site."
          : "Serviço indisponível — some da home, da listagem e da página pública."
      );
    },
    onError: () => toast.error("Erro ao atualizar disponibilidade."),
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
            <CmsRow
              key={item.slug}
              item={item}
              toggling={toggleMutation.isPending}
              onToggle={(isActive) =>
                toggleMutation.mutate({ id: item.product_id, isActive })
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
