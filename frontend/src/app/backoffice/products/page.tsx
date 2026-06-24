"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { adminService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/compound/page-header";
import { EmptyState } from "@/components/compound/empty-state";
import { ProductCard } from "@/components/backoffice/product-card";
import { ProductFormModal } from "@/components/backoffice/product-form-modal";
import { PricingManagerModal } from "@/components/backoffice/pricing-manager-modal";
import type { ProductFormData } from "@/components/backoffice/product-form-modal";
import type { PricingFormData } from "@/components/backoffice/pricing-manager-modal";
import { Package, Plus } from "lucide-react";
import type { Product } from "@/types";

export default function BackofficeProductsPage() {
  const qc = useQueryClient();
  const [editTarget, setEditTarget] = useState<Product | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [pricingProduct, setPricingProduct] = useState<Product | null>(null);

  const { data: products = [], isLoading } = useQuery<Product[]>({
    queryKey: ["admin-products"],
    queryFn: adminService.listProducts,
    staleTime: 60_000,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      adminService.toggleProduct(id, isActive),
    onSuccess: (updated) => {
      qc.setQueryData<Product[]>(["admin-products"], (prev) =>
        prev?.map((p) => (p.id === updated.id ? updated : p)) ?? []
      );
      toast.success(updated.is_active ? "Produto ativado." : "Produto desativado.");
    },
    onError: () => toast.error("Erro ao atualizar produto."),
  });

  const createMutation = useMutation({
    mutationFn: adminService.createProduct,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-products"] });
      setShowCreate(false);
      toast.success("Produto criado.");
    },
    onError: () => toast.error("Erro ao criar produto."),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProductFormData }) =>
      adminService.updateProduct(id, data),
    onSuccess: (updated) => {
      qc.setQueryData<Product[]>(["admin-products"], (prev) =>
        prev?.map((p) => (p.id === updated.id ? updated : p)) ?? []
      );
      setEditTarget(null);
      toast.success("Produto atualizado.");
    },
    onError: () => toast.error("Erro ao atualizar produto."),
  });

  const createPricingMutation = useMutation({
    mutationFn: ({ productId, data }: { productId: string; data: PricingFormData }) =>
      adminService.createPricing(productId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-products"] });
      toast.success("Precificação criada.");
    },
    onError: () => toast.error("Erro ao criar precificação."),
  });

  const updatePricingMutation = useMutation({
    mutationFn: ({ productId, pricingId, data }: { productId: string; pricingId: string; data: Omit<PricingFormData, "billing_cycle"> }) =>
      adminService.updatePricing(productId, pricingId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-products"] });
      toast.success("Precificação atualizada.");
    },
    onError: () => toast.error("Erro ao atualizar precificação."),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <PageHeader title="Produtos" description="Catálogo de produtos e planos disponíveis" />
        <Button variant="primary" size="sm" onClick={() => setShowCreate(true)}>
          <Plus size={14} className="mr-1.5" />
          Novo produto
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-24 w-full rounded-xl" />)}
        </div>
      ) : products.length === 0 ? (
        <EmptyState icon={Package} title="Nenhum produto cadastrado" description="Produtos criados no backend aparecerão aqui." />
      ) : (
        <div className="space-y-3">
          {products.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              toggling={toggleMutation.isPending}
              onToggle={(isActive) => toggleMutation.mutate({ id: product.id, isActive })}
              onEdit={() => setEditTarget(product)}
              onManagePricings={() => setPricingProduct(product)}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <ProductFormModal
          loading={createMutation.isPending}
          onSubmit={(data) => createMutation.mutate(data)}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {editTarget && (
        <ProductFormModal
          initial={editTarget}
          loading={updateMutation.isPending}
          onSubmit={(data) => updateMutation.mutate({ id: editTarget.id, data })}
          onCancel={() => setEditTarget(null)}
        />
      )}

      {pricingProduct && (
        <PricingManagerModal
          product={pricingProduct}
          creating={createPricingMutation.isPending}
          updating={updatePricingMutation.isPending}
          onCreatePricing={(data) => createPricingMutation.mutate({ productId: pricingProduct.id, data })}
          onUpdatePricing={(pricingId, data) =>
            updatePricingMutation.mutate({ productId: pricingProduct.id, pricingId, data })
          }
          onClose={() => setPricingProduct(null)}
        />
      )}
    </div>
  );
}
