import { cn } from "@/lib/utils";

type PlanTier = "free" | "starter" | "business" | "enterprise";

interface PlanBadgeProps {
  tier?: PlanTier;
  name?: string;
  className?: string;
}

const tierConfig: Record<PlanTier, { label: string; classes: string }> = {
  free:       { label: "Free",       classes: "bg-surface-4 text-text-secondary border-border-subtle" },
  starter:    { label: "Starter",    classes: "bg-info-muted text-info border border-info/20" },
  business:   { label: "Business",   classes: "bg-brand-accent/12 text-brand-accent border border-brand-accent/20" },
  enterprise: { label: "Enterprise", classes: "bg-warning-muted text-warning border border-warning/20" },
};

function detectTier(name?: string): PlanTier {
  if (!name) return "starter";
  const lower = name.toLowerCase();
  if (lower.includes("enterprise")) return "enterprise";
  if (lower.includes("business")) return "business";
  if (lower.includes("starter")) return "starter";
  return "free";
}

export function PlanBadge({ tier, name, className }: PlanBadgeProps) {
  const resolvedTier = tier ?? detectTier(name);
  const config = tierConfig[resolvedTier];

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border uppercase tracking-wider",
        config.classes,
        className
      )}
    >
      {name ?? config.label}
    </span>
  );
}
