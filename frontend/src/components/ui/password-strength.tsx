"use client";

import { cn } from "@/lib/utils";

interface PasswordStrengthProps {
  password: string;
  className?: string;
}

interface StrengthResult {
  score: 0 | 1 | 2 | 3 | 4;
  label: string;
  color: string;
}

function evaluate(password: string): StrengthResult {
  if (!password) return { score: 0, label: "", color: "" };

  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  // cap at 4
  const capped = Math.min(4, score) as 0 | 1 | 2 | 3 | 4;

  const map: Record<1 | 2 | 3 | 4, { label: string; color: string }> = {
    1: { label: "Muito fraca", color: "bg-danger" },
    2: { label: "Fraca", color: "bg-warning" },
    3: { label: "Boa", color: "bg-info" },
    4: { label: "Forte", color: "bg-success" },
  };

  return capped === 0
    ? { score: 0, label: "", color: "" }
    : { score: capped, ...map[capped] };
}

export function PasswordStrength({ password, className }: PasswordStrengthProps) {
  const { score, label, color } = evaluate(password);

  if (!password) return null;

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={cn(
              "h-1 flex-1 rounded-full transition-colors duration-300",
              i <= score ? color : "bg-surface-3"
            )}
          />
        ))}
      </div>
      {label && (
        <p className={cn("text-xs", score <= 1 ? "text-danger" : score === 2 ? "text-warning" : score === 3 ? "text-info" : "text-success")}>
          {label}
        </p>
      )}
    </div>
  );
}
