import type { Metadata } from "next";
import type { Components } from "react-markdown";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft } from "lucide-react";
import { LandingNav } from "@/components/marketing/nav";
import { Footer } from "@/components/marketing/footer";
import { fetchBlogPost } from "@/lib/blog";

export const revalidate = 60;

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://app.papermoon.com.br";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = await fetchBlogPost(slug);
  if (!post) return {};

  const title = post.meta_title || post.title;
  const description = post.meta_description || post.excerpt;
  const pageUrl = `${SITE_URL}/blog/${slug}`;
  const ogImageUrl =
    `${SITE_URL}/api/og?` +
    new URLSearchParams({ title: post.title, desc: description, tag: "Blog PaperMoon" }).toString();

  return {
    title: `${title} — Blog PaperMoon`,
    description,
    alternates: { canonical: pageUrl },
    openGraph: {
      title: post.title,
      description,
      url: pageUrl,
      siteName: "PaperMoon",
      type: "article",
      publishedTime: post.published_at ?? undefined,
      images: [{ url: post.cover_image_url ?? ogImageUrl, width: 1200, height: 630, alt: post.cover_image_alt || post.title }],
    },
    twitter: {
      card: "summary_large_image",
      title: post.title,
      description,
      images: [post.cover_image_url ?? ogImageUrl],
    },
  };
}

/* ── Renderização do Markdown ─────────────────────────────────────── */
// Sem plugin de tipografia no projeto — estiliza cada elemento explicitamente
// (mesma abordagem do preview em backoffice/blog/[id]).
const ARTICLE_COMPONENTS: Components = {
  h1: ({ children }) => <h1 className="text-2xl sm:text-3xl font-bold text-text-primary mt-10 mb-4 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-xl sm:text-2xl font-bold text-text-primary mt-9 mb-3 first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="text-lg font-semibold text-text-primary mt-7 mb-2 first:mt-0">{children}</h3>,
  p: ({ children }) => <p className="text-sm sm:text-base text-text-secondary leading-relaxed mb-4">{children}</p>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-brand-accent hover:underline">
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="list-disc list-outside pl-5 text-sm sm:text-base text-text-secondary space-y-1.5 mb-4">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-outside pl-5 text-sm sm:text-base text-text-secondary space-y-1.5 mb-4">{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-brand-accent/40 pl-4 text-text-tertiary italic mb-4">{children}</blockquote>
  ),
  code: ({ children }) => (
    <code className="rounded bg-surface-2 px-1.5 py-0.5 text-[13px] font-mono text-text-primary">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="rounded-xl bg-surface-2 px-4 py-3.5 text-[13px] font-mono text-text-primary overflow-x-auto mb-4">
      {children}
    </pre>
  ),
  strong: ({ children }) => <strong className="font-semibold text-text-primary">{children}</strong>,
  hr: () => <hr className="border-border-subtle my-8" />,
  img: ({ src, alt }) =>
    typeof src === "string" ? (
      // eslint-disable-next-line @next/next/no-img-element -- markdown-authored, dimensões desconhecidas em tempo de build
      <img src={src} alt={alt ?? ""} className="rounded-xl my-4 w-full h-auto" />
    ) : null,
  table: ({ children }) => (
    <div className="overflow-x-auto mb-4">
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-border-subtle px-3 py-2 text-left text-xs font-semibold text-text-tertiary">{children}</th>
  ),
  td: ({ children }) => <td className="border border-border-subtle px-3 py-2 text-text-secondary">{children}</td>,
};

function formatDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" });
}

export default async function BlogPostPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const post = await fetchBlogPost(slug);
  if (!post) notFound();

  const pageUrl = `${SITE_URL}/blog/${slug}`;
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.meta_description || post.excerpt,
    image: post.cover_image_url ?? undefined,
    author: { "@type": "Person", name: post.author_name },
    publisher: { "@type": "Organization", name: "PaperMoon" },
    datePublished: post.published_at ?? undefined,
    mainEntityOfPage: pageUrl,
  };

  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <LandingNav />

      <article className="pt-28 pb-20">
        <div className="max-w-2xl mx-auto px-6">
          <Link
            href="/blog"
            className="inline-flex items-center gap-1.5 text-xs text-text-tertiary hover:text-text-secondary transition-colors mb-8"
          >
            <ArrowLeft size={12} />
            Blog
          </Link>

          <header className="mb-8 space-y-4">
            <h1 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">{post.title}</h1>
            <p className="text-sm text-text-tertiary">
              {formatDate(post.published_at)} · {post.author_name}
            </p>
          </header>

          {post.cover_image_url && (
            <div className="rounded-2xl overflow-hidden mb-10">
              <Image
                src={post.cover_image_url}
                alt={post.cover_image_alt || post.title}
                width={1200}
                height={630}
                className="w-full h-auto"
                priority
              />
            </div>
          )}

          <ReactMarkdown remarkPlugins={[remarkGfm]} components={ARTICLE_COMPONENTS}>
            {post.body}
          </ReactMarkdown>

          <div className="mt-14 pt-8 border-t border-border-subtle text-center">
            <Link
              href="/blog"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-accent hover:underline"
            >
              <ArrowLeft size={13} />
              Ver todos os posts
            </Link>
          </div>
        </div>
      </article>

      <Footer idSuffix={`blog-${slug}`} />
    </div>
  );
}
