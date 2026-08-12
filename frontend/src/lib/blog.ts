/** Types mirroring the Django blog serializer output for public posts. */

export interface BlogTag {
  name: string;
  slug: string;
}

export interface BlogPostSummary {
  slug: string;
  title: string;
  excerpt: string;
  cover_image_url: string | null;
  cover_image_alt: string;
  author_name: string;
  published_at: string | null;
  reading_time: number;
  tags: BlogTag[];
}

export interface BlogPostFull extends BlogPostSummary {
  body: string;
  meta_title: string;
  meta_description: string;
}

export interface PaginatedBlogPosts {
  count: number;
  next: string | null;
  previous: string | null;
  results: BlogPostSummary[];
}

const EMPTY_PAGE: PaginatedBlogPosts = { count: 0, next: null, previous: null, results: [] };

// Same reasoning as fetchCmsServicePage in lib/cms.ts — call Django directly,
// avoids self-referential HTTP inside the container (localhost resolves to
// IPv6 ::1 in Docker but Next.js only binds IPv4 0.0.0.0:3000).
const DJANGO_URL = process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

/** Fetch a page of published blog posts, optionally filtered by tag slug.
 * Never throws — returns an empty page on failure. */
export async function fetchBlogPosts(page = 1, tag?: string): Promise<PaginatedBlogPosts> {
  try {
    const params = new URLSearchParams({ page: String(page) });
    if (tag) params.set("tag", tag);
    const res = await fetch(`${DJANGO_URL}/blog/?${params.toString()}`, {
      next: { revalidate: 60, tags: ["blog-posts"] },
    });
    if (!res.ok) return EMPTY_PAGE;
    const json = await res.json();
    // Unwrap Django unified response envelope { success, data, error }
    return (json?.data ?? json) as PaginatedBlogPosts;
  } catch {
    return EMPTY_PAGE;
  }
}

/** Fetch a single published post by slug. Returns null if not found (or a draft).
 *
 * Sem ISR aqui de propósito (`cache: "no-store"`) — o Next.js App Router (14.2,
 * confirmado com testes manuais contra o build standalone real) não invalida o
 * Full Route Cache quando uma rota que ANTES renderizou com sucesso passa a
 * chamar `notFound()`: nem `revalidateTag`/`revalidatePath` explícitos nem a
 * janela passiva de `revalidate` conseguem purgar esse estado — a página fica
 * presa servindo o último HTML publicado até o próximo deploy. Isso faria um
 * post despublicado ("Voltar a rascunho") ou excluído continuar publicamente
 * acessível na URL antiga por tempo indeterminado. `fetchBlogPosts` (listagem)
 * não tem esse problema — só a transição pra notFound() de uma rota dinâmica
 * individual é afetada — por isso só o detalhe abre mão do cache. */
export async function fetchBlogPost(slug: string): Promise<BlogPostFull | null> {
  try {
    const res = await fetch(`${DJANGO_URL}/blog/${slug}/`, { cache: "no-store" });
    if (!res.ok) return null;
    const json = await res.json();
    return (json?.data ?? json) as BlogPostFull | null;
  } catch {
    return null;
  }
}

const WORDS_PER_MINUTE = 200; // média de leitura em português — mesma ordem de grandeza usada por Medium/dev.to

/** Estimativa simples por contagem de palavras do Markdown cru — não vale a
 * pena parsear a árvore só pra isso, a mesma aproximação que sites de blog
 * consolidados usam. Mínimo de 1 minuto mesmo pra posts bem curtos. */
export function estimateReadingTime(markdown: string): number {
  const words = markdown.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / WORDS_PER_MINUTE));
}
