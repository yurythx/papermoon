"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { cn } from "@/lib/utils";

interface CopyButtonProps {
  value: string;
  label?: string;
  className?: string;
}

/**
 * Extraído do padrão já repetido em três lugares do dashboard (api-keys,
 * licenses/[id], backoffice/settings) — sempre "copia pro clipboard + mostra
 * feedback por 2s", só variando entre ícone puro e ícone+label. Este cobre
 * os dois: passe `label` pra ter texto, ou omita pra um botão só de ícone
 * (útil como `rightElement` de um Input readOnly).
 */
export function CopyButton({ value, label, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={label ? undefined : "Copiar"}
      className={cn(
        "inline-flex items-center gap-1.5 text-text-tertiary hover:text-text-secondary transition-colors cursor-pointer",
        label && "text-xs font-medium",
        className
      )}
    >
      {copied ? <Check size={label ? 13 : 14} className="text-success" /> : <Copy size={label ? 13 : 14} />}
      {label && (copied ? "Copiado" : label)}
    </button>
  );
}
