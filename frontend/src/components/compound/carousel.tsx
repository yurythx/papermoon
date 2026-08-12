"use client";

import { Children, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface CarouselProps {
  /** Cada filho direto vira um slide. */
  children: ReactNode;
  className?: string;
  /** Largura de cada slide (className aplicado no wrapper do slide) — ex: "w-[320px]". */
  slideClassName?: string;
  ariaLabel?: string;
}

// Scroll-snap + CSS puro, sem lib de carrossel (mesma filosofia de baixa
// dependência do resto do projeto — ver components/compound/code-block.tsx).
// Controles em pill único ("‹ 1/5 ›"), igual ao carrossel de "Novidades" da AWS.
export function Carousel({ children, className, slideClassName, ariaLabel = "Carrossel" }: CarouselProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const slideRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [index, setIndex] = useState(0);
  const slides = Children.toArray(children);
  const count = slides.length;

  const scrollToIndex = useCallback(
    (target: number) => {
      const clamped = Math.max(0, Math.min(count - 1, target));
      const el = slideRefs.current[clamped];
      const track = trackRef.current;
      if (el && track) {
        track.scrollTo({ left: el.offsetLeft - track.offsetLeft, behavior: "smooth" });
      }
    },
    [count]
  );

  // Acompanha o slide mais próximo enquanto o usuário arrasta/rola manualmente
  // (não só quando clica nas setas) — pra manter o contador "1/5" sincronizado.
  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const scrollLeft = track.scrollLeft;
        let nearest = 0;
        let nearestDist = Infinity;
        slideRefs.current.forEach((el, i) => {
          if (!el) return;
          const dist = Math.abs(el.offsetLeft - track.offsetLeft - scrollLeft);
          if (dist < nearestDist) {
            nearestDist = dist;
            nearest = i;
          }
        });
        setIndex(nearest);
      });
    };
    track.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      track.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  if (count === 0) return null;

  return (
    <div className={cn("relative", className)} role="region" aria-label={ariaLabel}>
      <div ref={trackRef} className="flex gap-4 overflow-x-auto snap-x snap-mandatory no-scrollbar scroll-smooth">
        {slides.map((slide, i) => (
          <div
            key={i}
            ref={(el) => {
              slideRefs.current[i] = el;
            }}
            className={cn("shrink-0 snap-center", slideClassName)}
          >
            {slide}
          </div>
        ))}
      </div>

      {count > 1 && (
        <div className="flex items-center justify-center mt-6">
          <div className="inline-flex items-center gap-1 rounded-full bg-surface-2 border border-border-subtle px-1.5 py-1.5">
            <button
              type="button"
              onClick={() => scrollToIndex(index - 1)}
              disabled={index === 0}
              aria-label="Anterior"
              className="w-7 h-7 rounded-full flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors disabled:opacity-30 disabled:pointer-events-none"
            >
              <ChevronLeft size={15} />
            </button>
            <span aria-live="polite" className="text-xs font-semibold text-text-secondary tabular-nums px-1.5 min-w-[3rem] text-center">
              {index + 1} / {count}
            </span>
            <button
              type="button"
              onClick={() => scrollToIndex(index + 1)}
              disabled={index === count - 1}
              aria-label="Próximo"
              className="w-7 h-7 rounded-full flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors disabled:opacity-30 disabled:pointer-events-none"
            >
              <ChevronRight size={15} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
