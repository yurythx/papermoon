import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// RegExp construída com \u escape (não literal colado no arquivo) por
// segurança de encoding entre editores/terminais.
const COMBINING_DIACRITICS_RE = new RegExp("[\\u0300-\\u036f]", "g");

/** "Título com Acentuação" -> "titulo-com-acentuacao". Mesma lógica antes
 * duplicada em blog-post-form-modal.tsx e backoffice/integrations/keycloak —
 * consolidada aqui pra não virar uma terceira cópia a cada form novo. */
export function slugify(value: string): string {
  return value
    .normalize("NFD")
    .replace(COMBINING_DIACRITICS_RE, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
