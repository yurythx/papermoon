import { cn } from "@/lib/utils";

interface TimeProgressProps {
  startDate: string | Date;
  endDate: string | Date;
  showLabel?: boolean;
  className?: string;
}

function getDaysRemaining(endDate: string | Date): number {
  const end = new Date(endDate);
  const now = new Date();
  const diff = end.getTime() - now.getTime();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

function getProgress(startDate: string | Date, endDate: string | Date): number {
  const start = new Date(startDate).getTime();
  const end = new Date(endDate).getTime();
  const now = Date.now();
  if (end <= start) return 100;
  const elapsed = now - start;
  const total = end - start;
  return Math.min(100, Math.max(0, (elapsed / total) * 100));
}

export function TimeProgress({ startDate, endDate, showLabel = true, className }: TimeProgressProps) {
  const daysLeft = getDaysRemaining(endDate);
  const progress = getProgress(startDate, endDate);
  const remaining = 100 - progress;

  const isExpired = daysLeft === 0;
  const isCritical = daysLeft > 0 && daysLeft <= 7;
  const isWarning = daysLeft > 7 && daysLeft <= 20;

  const trackClass = "bg-surface-4";
  const fillClass = isExpired
    ? "bg-danger/40"
    : isCritical
    ? "bg-danger animate-pulse-soft"
    : isWarning
    ? "bg-warning animate-pulse-soft"
    : "bg-gradient-to-r from-brand-emerald to-brand-cyan";

  return (
    <div className={cn("space-y-1", className)}>
      <div
        role="progressbar"
        aria-valuenow={remaining}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${daysLeft} dias restantes`}
        className={cn("h-1.5 rounded-full overflow-hidden", trackClass)}
      >
        <div
          className={cn("h-full rounded-full transition-all duration-600", fillClass)}
          style={{ width: `${remaining}%` }}
        />
      </div>
      {showLabel && (
        <p
          className={cn(
            "text-xs tabular-nums",
            isExpired ? "text-danger" :
            isCritical ? "text-danger" :
            isWarning ? "text-warning" :
            "text-text-tertiary"
          )}
        >
          {isExpired
            ? "Expirado"
            : `${daysLeft} dia${daysLeft !== 1 ? "s" : ""} restante${daysLeft !== 1 ? "s" : ""}`}
        </p>
      )}
    </div>
  );
}
