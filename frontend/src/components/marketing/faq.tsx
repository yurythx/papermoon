"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { LANDING_FAQS } from "@/lib/faq-content";

export function LandingFAQ() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="space-y-2">
      {LANDING_FAQS.map((item, i) => (
        <div
          key={i}
          className={cn(
            "border rounded-xl overflow-hidden transition-colors duration-200",
            open === i
              ? "bg-surface-1 border-brand-accent/30"
              : "bg-surface-1 border-border-subtle hover:border-border-default"
          )}
        >
          <button
            onClick={() => setOpen(open === i ? null : i)}
            className="w-full flex items-center justify-between px-6 py-4 text-left gap-4"
          >
            <span className={cn("text-sm font-medium transition-colors", open === i ? "text-text-primary" : "text-text-secondary")}>
              {item.q}
            </span>
            <ChevronDown
              size={15}
              className={cn(
                "shrink-0 transition-all duration-200",
                open === i ? "rotate-180 text-brand-accent" : "text-text-tertiary"
              )}
            />
          </button>
          {open === i && (
            <div className="px-6 pb-5">
              <p className="text-sm text-text-secondary leading-relaxed">{item.a}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
