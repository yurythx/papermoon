import Link from "next/link";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { type LucideIcon, PackageSearch } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
    variant?: "primary" | "secondary";
  };
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon = PackageSearch,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center py-16 text-center", className)}>
      <div className="bg-surface-2 rounded-full p-5 mb-4 border border-border-subtle">
        <Icon size={28} className="text-text-tertiary" />
      </div>
      <h3 className="text-base font-semibold text-text-primary mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-text-secondary max-w-xs mb-6">{description}</p>
      )}
      {action && (
        action.href ? (
          <Link href={action.href}>
            <Button variant={action.variant ?? "secondary"} size="sm">{action.label}</Button>
          </Link>
        ) : (
          <Button variant={action.variant ?? "secondary"} size="sm" onClick={action.onClick}>
            {action.label}
          </Button>
        )
      )}
    </div>
  );
}
