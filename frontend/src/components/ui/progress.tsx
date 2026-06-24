import { cn } from "@/lib/utils";

interface ProgressProps {
  value: number;
  variant?: "default" | "warning" | "danger" | "success";
  className?: string;
  animated?: boolean;
}

const trackVariants = {
  default: "bg-surface-4",
  warning: "bg-surface-4",
  danger: "bg-surface-4",
  success: "bg-surface-4",
};

const fillVariants = {
  default: "bg-gradient-to-r from-brand-emerald to-brand-cyan",
  warning: "bg-warning",
  danger: "bg-danger",
  success: "bg-success",
};

export function Progress({ value, variant = "default", className, animated = false }: ProgressProps) {
  const clamped = Math.min(Math.max(value, 0), 100);

  return (
    <div
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cn("h-1.5 rounded-full overflow-hidden", trackVariants[variant], className)}
    >
      <div
        className={cn(
          "h-full rounded-full transition-all duration-600",
          fillVariants[variant],
          animated && variant === "warning" && "animate-pulse-soft",
          animated && variant === "danger" && "animate-pulse-soft"
        )}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
