import { Badge } from "@/components/ui/badge";
import { type BadgeVariant } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// Re-export BadgeVariant from badge for convenience
export type { BadgeVariant } from "@/components/ui/badge";

type LicenseStatus = "active" | "trial" | "expiring" | "expired" | "suspended" | "cancelled" | "grace_period";
type SubscriptionStatus = "trial" | "active" | "suspended" | "expired" | "grace_period" | "cancelled";
type CustomerStatus = "active" | "suspended" | "cancelled";
type InvoiceStatus = "pending" | "paid" | "overdue" | "cancelled";
type ServiceStatus = "provisioning" | "active" | "suspended" | "failed";

interface StatusBadgeProps {
  status: LicenseStatus | SubscriptionStatus | CustomerStatus | InvoiceStatus | ServiceStatus | string;
  className?: string;
}

const statusMap: Record<string, { label: string; variant: BadgeVariant; dot?: boolean }> = {
  // License / Subscription
  active:       { label: "Ativo", variant: "success", dot: true },
  trial:        { label: "Trial", variant: "info", dot: true },
  expiring:     { label: "Expirando", variant: "warning", dot: true },
  expired:      { label: "Expirado", variant: "danger", dot: true },
  suspended:    { label: "Suspenso", variant: "danger", dot: true },
  cancelled:    { label: "Cancelado", variant: "muted", dot: true },
  grace_period: { label: "Tolerância", variant: "warning", dot: true },
  // Invoice
  pending:      { label: "Pendente", variant: "warning", dot: true },
  paid:         { label: "Pago", variant: "success", dot: true },
  overdue:      { label: "Vencida", variant: "danger", dot: true },
  // Service
  provisioning: { label: "Provisionando", variant: "info", dot: true },
  failed:       { label: "Falhou", variant: "danger", dot: true },
  // Invitation
  accepted:     { label: "Aceito", variant: "success", dot: true },
  revoked:      { label: "Revogado", variant: "muted", dot: false },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusMap[status] ?? { label: status, variant: "muted" as BadgeVariant, dot: false };
  return (
    <Badge variant={config.variant} dot={config.dot} className={cn(className)}>
      {config.label}
    </Badge>
  );
}
