"use client";

import { useQuery } from "@tanstack/react-query";
import { productService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { ShoppingBag, Zap, Mail } from "lucide-react";
import type { Product } from "@/types";

const SERVICE_LABELS: Record<string, string> = {
  n8n: "n8n",
  chatwoot: "Chatwoot",
  meta_whatsapp: "WhatsApp API Meta",
  glpi: "GLPI Helpdesk",
  zabbix: "Zabbix",
  proxmox: "Proxmox VE",
  truenas: "TrueNAS",
  nextcloud: "Nextcloud",
  aapanel: "AAPanel",
  evolution_api: "Evolution API",
  tailscale: "Tailscale",
};

const CYCLE_LABEL: Record<string, string> = {
  monthly: "Mensal",
  annual: "Anual",
  lifetime: "Vitalício",
  one_time: "Cobrança Única",
};

export default function CatalogPage() {
  const { data: products, isLoading } = useQuery({
    queryKey: ["catalog"],
    queryFn: productService.catalog,
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Nossos Serviços"
        description="Conheça os serviços disponíveis — para contratar ou renovar, entre em contato com nossa equipe"
      />

      {/* Contact CTA banner */}
      <div className="flex items-center gap-4 rounded-xl border border-brand-accent/25 bg-brand-accent/5 px-5 py-4">
        <div className="w-9 h-9 rounded-lg bg-brand-accent/15 flex items-center justify-center shrink-0">
          <Mail size={16} className="text-brand-accent" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-text-primary">Quer contratar um novo serviço?</p>
          <p className="text-xs text-text-secondary mt-0.5">
            Entre em contato com nossa equipe — vamos negociar e configurar tudo para você.
          </p>
        </div>
        <a
          href="mailto:contato@papermoon.com.br"
          className="shrink-0 text-xs font-semibold text-brand-accent border border-brand-accent/30 px-4 py-2 rounded-lg hover:bg-brand-accent/10 transition-colors"
        >
          Falar com a equipe
        </a>
      </div>

      {isLoading ? (
        <CatalogSkeleton />
      ) : !products?.length ? (
        <EmptyState
          title="Nenhum serviço disponível"
          icon={ShoppingBag}
          description="O catálogo está sendo atualizado. Se você já souber o que precisa, nossa equipe pode indicar a melhor composição de serviços."
          action={{ label: "Falar com a equipe", href: "/#contato", variant: "primary" }}
        />
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {products.map((product) => (
            <ServiceCard key={product.id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}

function ServiceCard({ product }: { product: Product }) {
  const activePricings = product.pricings.filter((p) => p.is_active);

  return (
    <div className="bg-surface-1 border border-border-subtle rounded-xl p-5 flex flex-col hover:border-border-focus transition-all duration-150">
      {/* Header */}
      <div className="mb-4">
        <h2 className="text-base font-semibold text-text-primary">{product.name}</h2>
        {product.description && (
          <p className="text-sm text-text-secondary mt-1.5 line-clamp-3">{product.description}</p>
        )}
      </div>

      {/* Components */}
      {product.components.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-1.5 mb-2">
            <Zap size={11} className="text-text-tertiary" />
            <p className="text-xs font-medium text-text-tertiary">Inclui</p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {product.components.map((c) => (
              <Badge key={c.id} variant="info">
                {SERVICE_LABELS[c.service_key] ?? c.service_key}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Pricing — read-only */}
      {activePricings.length > 0 && (
        <div className="mt-auto pt-4 border-t border-border-subtle space-y-1.5">
          {activePricings.map((pricing) => (
            <div key={pricing.id} className="flex items-center justify-between">
              <span className="text-xs text-text-tertiary">
                {CYCLE_LABEL[pricing.billing_cycle] ?? pricing.billing_cycle}
              </span>
              <span className="text-sm font-semibold text-text-primary tabular-nums">
                R$ {parseFloat(pricing.amount).toFixed(2)}
                {pricing.billing_cycle === "monthly" && (
                  <span className="text-xs font-normal text-text-tertiary">/mês</span>
                )}
                {pricing.billing_cycle === "annual" && (
                  <span className="text-xs font-normal text-text-tertiary">/ano</span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CatalogSkeleton() {
  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-surface-1 border border-border-subtle rounded-xl p-5 space-y-3">
          <Skeleton className="h-5 w-2/3" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-4/5" />
          <div className="pt-4 border-t border-border-subtle space-y-2">
            <Skeleton className="h-4 w-full rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}
