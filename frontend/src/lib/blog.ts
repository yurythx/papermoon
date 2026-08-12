/** Types mirroring the Django blog serializer output for public posts. */

export interface BlogPostSummary {
  slug: string;
  title: string;
  excerpt: string;
  cover_image_url: string | null;
  cover_image_alt: string;
  author_name: string;
  published_at: string | null;
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

/** Fetch a page of published blog posts. Never throws — returns an empty page on failure. */
export async function fetchBlogPosts(page = 1): Promise<PaginatedBlogPosts> {
  try {
    const res = await fetch(`${DJANGO_URL}/blog/?page=${page}`, {
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

/** Fetch a single published post by slug. Returns null if not found (or a draft). */
export async function fetchBlogPost(slug: string): Promise<BlogPostFull | null> {
  try {
    const res = await fetch(`${DJANGO_URL}/blog/${slug}/`, {
      next: { revalidate: 60, tags: [`blog-post-${slug}`] },
    });
    if (!res.ok) return null;
    const json = await res.json();
    return (json?.data ?? json) as BlogPostFull | null;
  } catch {
    return null;
  }
}
