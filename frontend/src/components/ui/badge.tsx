import { cn } from "@/lib/utils";

export type BadgeVariant = "default" | "success" | "warning" | "danger" | "info" | "accent" | "muted";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  dot?: boolean;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-surface-4 text-text-secondary border-border-subtle",
  success: "bg-success-muted text-success border border-success/20",
  warning: "bg-warning-muted text-warning border border-warning/20",
  danger:  "bg-danger-muted text-danger border border-danger/20",
  info:    "bg-info-muted text-info border border-info/20",
  accent:  "bg-brand-accent/12 text-brand-accent border border-brand-accent/20",
  muted:   "bg-surface-3 text-text-tertiary border-border-subtle",
};

const dotColors: Record<BadgeVariant, string> = {
  default: "bg-text-tertiary",
  success: "bg-success",
  warning: "bg-warning",
  danger:  "bg-danger",
  info:    "bg-info",
  accent:  "bg-brand-accent",
  muted:   "bg-text-tertiary",
};

export function Badge({ children, variant = "default", dot = false, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium border",
        variantClasses[variant],
        className
      )}
    >
      {dot && (
        <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", dotColors[variant])} />
      )}
      {children}
    </span>
  );
}
