"use client";

import Image from "next/image";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { useState, useEffect, useCallback, useId, useRef } from "react";

import type { GalleryImage } from "@/lib/merge-service";

interface Props {
  images: GalleryImage[];
  colorBorder: string;
}

export function ServiceGallery({ images, colorBorder }: Props) {
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);
  const dialogId = useId();
  const titleId = `${dialogId}-title`;
  const descriptionId = `${dialogId}-description`;
  const lightboxRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const prev = useCallback(() => {
    setIndex((i) => (i - 1 + images.length) % images.length);
  }, [images.length]);

  const next = useCallback(() => {
    setIndex((i) => (i + 1) % images.length);
  }, [images.length]);

  useEffect(() => {
    if (!open) return;

    previousFocusRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;

    const frame = window.requestAnimationFrame(() => {
      lightboxRef.current?.focus();
    });

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
      if (e.key === "Tab") {
        const panel = lightboxRef.current;
        if (!panel) return;

        const focusableElements = Array.from(
          panel.querySelectorAll<HTMLElement>(
            "button:not([disabled]), a[href], [tabindex]:not([tabindex='-1'])"
          )
        );

        if (focusableElements.length === 0) {
          e.preventDefault();
          panel.focus();
          return;
        }

        const first = focusableElements[0];
        const last = focusableElements[focusableElements.length - 1];
        const active = document.activeElement as HTMLElement | null;

        if (e.shiftKey && active === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && active === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => {
      window.cancelAnimationFrame(frame);
      document.body.style.overflow = originalOverflow;
      window.removeEventListener("keydown", handler);
      previousFocusRef.current?.focus();
    };
  }, [open, prev, next]);

  if (images.length === 0) return null;

  return (
    <>
      {/* Thumbnail grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {images.map((img, i) => (
          <button
            key={img.url}
            onClick={() => {
              setIndex(i);
              setOpen(true);
            }}
            className={`group relative rounded-xl overflow-hidden border ${colorBorder} shadow-md hover:shadow-xl transition-shadow cursor-zoom-in`}
            aria-label={img.alt || `Imagem ${i + 1}`}
          >
            <div className="relative aspect-video w-full">
              <Image
                src={img.url}
                alt={img.alt}
                fill
                sizes="(max-width: 640px) 50vw, 33vw"
                className="object-cover group-hover:scale-105 transition-transform duration-300"
              />
            </div>
            {img.caption && (
              <p className="absolute inset-x-0 bottom-0 px-3 py-1.5 text-[10px] text-white bg-black/60 truncate">
                {img.caption}
              </p>
            )}
          </button>
        ))}
      </div>

      {/* Lightbox */}
      {open && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        >
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-accent focus-visible:ring-offset-2 focus-visible:ring-offset-black"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>

          {images.length > 1 && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                prev();
              }}
              className="absolute left-4 p-3 rounded-full bg-white/10 hover:bg-white/20 transition-colors text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-accent focus-visible:ring-offset-2 focus-visible:ring-offset-black"
              aria-label="Anterior"
            >
              <ChevronLeft size={22} />
            </button>
          )}

          <div
            ref={lightboxRef}
            tabIndex={-1}
            aria-labelledby={titleId}
            aria-describedby={descriptionId}
            className="relative max-h-[85vh] max-w-[90vw] w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id={titleId} className="sr-only">
              Galeria de imagens do serviço
            </h2>
            <Image
              src={images[index].url}
              alt={images[index].alt}
              width={1200}
              height={720}
              className="object-contain max-h-[80vh] w-full rounded-xl shadow-2xl"
              priority
            />
            {images[index].caption && (
              <p id={descriptionId} className="text-center text-sm text-white/70 mt-3 px-4">
                {images[index].caption}
              </p>
            )}
            {!images[index].caption && (
              <p id={descriptionId} className="sr-only">
                Imagem {index + 1} de {images.length}
              </p>
            )}
            {images.length > 1 && (
              <p className="text-center text-xs text-white/40 mt-1">
                {index + 1} / {images.length}
              </p>
            )}
          </div>

          {images.length > 1 && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                next();
              }}
              className="absolute right-4 p-3 rounded-full bg-white/10 hover:bg-white/20 transition-colors text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-accent focus-visible:ring-offset-2 focus-visible:ring-offset-black"
              aria-label="Próxima"
            >
              <ChevronRight size={22} />
            </button>
          )}
        </div>
      )}
    </>
  );
}
