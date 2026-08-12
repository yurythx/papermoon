import { NextResponse } from "next/server";
import { fetchBlogPosts } from "@/lib/blog";

// Mesmo revalidate dos outros caches de blog (lib/blog.ts, sitemap.ts) — ISR
// via /api/revalidate mantém isso fresco entre publicações também.
export const revalidate = 60;

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://app.papermoon.com.br";

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export async function GET() {
  // Só a página mais recente (até 20 posts) — padrão de feed RSS, leitores
  // de feed não esperam o arquivo inteiro do blog.
  const { results: posts } = await fetchBlogPosts(1);

  const items = posts
    .map((post) => {
      const url = `${SITE_URL}/blog/${post.slug}`;
      const pubDate = (post.published_at ? new Date(post.published_at) : new Date()).toUTCString();
      const categories = post.tags.map((t) => `\n      <category>${escapeXml(t.name)}</category>`).join("");
      return `
    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <description>${escapeXml(post.excerpt)}</description>
      <dc:creator>${escapeXml(post.author_name)}</dc:creator>
      <pubDate>${pubDate}</pubDate>${categories}
    </item>`;
    })
    .join("");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Blog PaperMoon</title>
    <link>${SITE_URL}/blog</link>
    <atom:link href="${SITE_URL}/blog/rss.xml" rel="self" type="application/rss+xml" />
    <description>Melhores práticas, implementações e novidades sobre os serviços que a PaperMoon instala, configura e mantém.</description>
    <language>pt-BR</language>${items}
  </channel>
</rss>
`;

  return new NextResponse(xml, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "public, max-age=0, s-maxage=3600",
    },
  });
}
