import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Newspaper } from "lucide-react";
import { LandingNav } from "@/components/marketing/nav";
import { Footer } from "@/components/marketing/footer";
import { cardClass } from "@/components/ui/card";
import { ArrowLink } from "@/components/compound/arrow-link";
import { fetchBlogPosts } from "@/lib/blog";

export const revalidate = 60;

const PAGE_SIZE = 20; // mirror do PAGE_SIZE global do DRF (core/settings/base.py)
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://app.papermoon.com.br";

const _breadcrumbSchema = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    { "@type": "ListItem", position: 1, name: "Início", item: SITE_URL },
    { "@type": "ListItem", position: 2, name: "Blog", item: `${SITE_URL}/blog` },
  ],
};

export const metadata: Metadata = {
  title: "Blog — PaperMoon",
  description:
    "Melhores práticas, implementações e novidades sobre os serviços de TI gerenciados pela PaperMoon.",
  alternates: { canonical: `${SITE_URL}/blog` },
  openGraph: {
    title: "Blog — PaperMoon",
    description: "Melhores práticas, implementações e novidades sobre os serviços da PaperMoon.",
    url: `${SITE_URL}/blog`,
    siteName: "PaperMoon",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Blog — PaperMoon",
    description: "Melhores práticas, implementações e novidades sobre os serviços da PaperMoon.",
  },
};

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
}

export default async function BlogIndexPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, Number(pageParam) || 1);
  const { results: posts, count } = await fetchBlogPosts(page);
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE));

  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(_breadcrumbSchema) }} />
      <LandingNav />

      {/* Hero */}
      <section className="pt-32 pb-16 border-b border-border-subtle">
        <div className="max-w-5xl mx-auto px-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors mb-8"
          >
            <ArrowLeft size={12} />
            Voltar para o início
          </Link>

          <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">
            Conteúdo
          </p>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">Blog</h1>
          <p className="text-text-secondary max-w-xl text-sm leading-relaxed">
            Melhores práticas, implementações e novidades sobre os serviços que a PaperMoon
            instala, configura e mantém para você.
          </p>
        </div>
      </section>

      {/* Lista de posts */}
      <div className="max-w-5xl mx-auto px-6 py-16">
        {posts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
            <Newspaper size={28} className="text-text-tertiary" />
            <p className="text-sm text-text-secondary">Ainda não publicamos nenhum post.</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {posts.map((post) => (
              <Link
                key={post.slug}
                href={`/blog/${post.slug}`}
                className={cardClass({ interactive: true, className: "group flex flex-col p-0 overflow-hidden" })}
              >
                <div className="aspect-video bg-surface-2 overflow-hidden flex items-center justify-center">
                  {post.cover_image_url ? (
                    <Image
                      src={post.cover_image_url}
                      alt={post.cover_image_alt || post.title}
                      width={480}
                      height={270}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <Newspaper size={24} className="text-text-tertiary" />
                  )}
                </div>
                <div className="flex-1 flex flex-col gap-2 p-5">
                  <p className="text-[11px] text-text-tertiary">
                    {formatDate(post.published_at)} · {post.author_name}
                  </p>
                  <h2 className="text-sm font-bold text-text-primary line-clamp-2 group-hover:text-brand-accent transition-colors">
                    {post.title}
                  </h2>
                  <p className="text-xs text-text-secondary leading-relaxed line-clamp-3 flex-1">
                    {post.excerpt}
                  </p>
                  <ArrowLink size="xs" className="mt-1">
                    Ler mais
                  </ArrowLink>
                </div>
              </Link>
            ))}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-4 mt-12">
            <Link
              href={page > 1 ? `/blog?page=${page - 1}` : "#"}
              aria-disabled={page <= 1}
              className={`text-xs font-semibold ${page <= 1 ? "text-text-tertiary pointer-events-none opacity-40" : "text-text-secondary hover:text-text-primary"}`}
            >
              ← Anterior
            </Link>
            <span className="text-xs text-text-tertiary">
              Página {page} de {totalPages}
            </span>
            <Link
              href={page < totalPages ? `/blog?page=${page + 1}` : "#"}
              aria-disabled={page >= totalPages}
              className={`text-xs font-semibold ${page >= totalPages ? "text-text-tertiary pointer-events-none opacity-40" : "text-text-secondary hover:text-text-primary"}`}
            >
              Próxima →
            </Link>
          </div>
        )}
      </div>

      <Footer idSuffix="blog" />
    </div>
  );
}
