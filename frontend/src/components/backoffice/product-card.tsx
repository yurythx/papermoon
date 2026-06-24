"use client";

import { memo } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Pencil, DollarSign } from "lucide-react";
import type { Product } from "@/types";

interface ProductCardProps {
  product: Product;
  toggling: boolean;
  onToggle: (isActive: boolean) => void;
  onEdit: () => void;
  onManagePricings: () => void;
}

export const ProductCard = memo(function ProductCard({
  product,
  toggling,
  onToggle,
  onEdit,
  onManagePricings,
}: ProductCardProps) {
  const monthlyPrice = product.pricings.find((p) => p.billing_cycle === "monthly");
  const annualPrice = product.pricings.find((p) => p.billing_cycle === "annual");
  const oneTimePrice = product.pricings.find((p) => p.billing_cycle === "one_time");

  return (
    <div className={`bg-surface-1 border border-border-subtle rounded-xl p-5 transition-opacity ${!product.is_active ? "opacity-50" : ""}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-text-primary">{product.name}</h3>
            <Badge variant={product.is_active ? "success" : "muted"}>
              {product.is_active ? "Ativo" : "Inativo"}
            </Badge>
          </div>

          {product.description && (
            <p className="text-sm text-text-secondary mt-1">{product.description}</p>
          )}

          {product.components.length > 0 && (
            <div className="flex gap-1.5 mt-2 flex-wrap">
              {product.components.map((c) => (
                <Badge key={c.id} variant="info">
                  {c.service_key}
                </Badge>
              ))}
            </div>
          )}

          {product.pricings.length > 0 && (
            <div className="flex gap-4 mt-3 flex-wrap">
              {oneTimePrice && (
                <div className="text-xs text-text-secondary">
                  <span className="font-semibold text-text-primary">
                    R$ {parseFloat(oneTimePrice.amount).toFixed(2)}
                  </span>
                  {" "}(única)
                </div>
              )}
              {monthlyPrice && (
                <div className="text-xs text-text-secondary">
                  <span className="font-semibold text-text-primary">
                    R$ {parseFloat(monthlyPrice.amount).toFixed(2)}
                  </span>
                  /mês
                  {monthlyPrice.trial_days > 0 && (
                    <Badge variant="info" className="ml-1.5">{monthlyPrice.trial_days}d trial</Badge>
                  )}
                </div>
              )}
              {annualPrice && (
                <div className="text-xs text-text-secondary">
                  <span className="font-semibold text-text-primary">
                    R$ {parseFloat(annualPrice.amount).toFixed(2)}
                  </span>
                  /ano
                </div>
              )}
              {(monthlyPrice ?? oneTimePrice) && ((monthlyPrice ?? oneTimePrice)!.max_api_calls ?? 0) > 0 && (
                <div className="text-xs text-text-tertiary">
                  até {((monthlyPrice ?? oneTimePrice)!.max_api_calls ?? 0).toLocaleString("pt-BR")} chamadas/mês
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" onClick={onManagePricings}>
            <DollarSign size={13} className="mr-1" />
            Preços
          </Button>
          <Button variant="ghost" size="sm" onClick={onEdit}>
            <Pencil size={13} className="mr-1" />
            Editar
          </Button>
          <Button
            variant={product.is_active ? "ghost" : "secondary"}
            size="sm"
            disabled={toggling}
            onClick={() => onToggle(!product.is_active)}
          >
            {product.is_active ? "Desativar" : "Ativar"}
          </Button>
        </div>
      </div>
    </div>
  );
});
