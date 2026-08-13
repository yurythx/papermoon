import type { MetadataRoute } from "next";
import { SERVICES } from "@/lib/services-content";
import { fetchBlogPosts } from "@/lib/blog";

const MAX_BLOG_SITEMAP_PAGES = 10; // teto de segurança (~200 posts) contra loop caso `next` nunca zere

async function fetchAllBlogSlugs(): Promise<{ slug: string; published_at: string | null }[]> {
  const all: { slug: string; published_at: string | null }[] = [];
  for (let page = 1; page <= MAX_BLOG_SITEMAP_PAGES; page++) {
    const { results, next } = await fetchBlogPosts(page);
    all.push(...results.map((p) => ({ slug: p.slug, published_at: p.published_at })));
    if (!next) break;
  }
  return all;
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://papermoon.cloud";

  const staticPages: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${baseUrl}/sobre`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${baseUrl}/termos`,
      lastModified: new Date(),
      changeFrequency: "yearly",
      priority: 0.3,
    },
    {
      url: `${baseUrl}/login`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.4,
    },
    {
      url: `${baseUrl}/register`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.6,
    },
    {
      url: `${baseUrl}/servicos`,
      lastModified: new Date(),
      changeFrequency: "weekly" as const,
      priority: 0.9,
    },
    {
      url: `${baseUrl}/forgot-password`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.3,
    },
    {
      url: `${baseUrl}/blog`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.7,
    },
  ];

  const servicePages: MetadataRoute.Sitemap = SERVICES.map((svc) => ({
    url: `${baseUrl}/servicos/${svc.slug}`,
    lastModified: new Date(),
    changeFrequency: "weekly" as const,
    priority: svc.comingSoon ? 0.5 : 0.9,
  }));

  const blogSlugs = await fetchAllBlogSlugs();
  const blogPages: MetadataRoute.Sitemap = blogSlugs.map((post) => ({
    url: `${baseUrl}/blog/${post.slug}`,
    lastModified: post.published_at ? new Date(post.published_at) : new Date(),
    changeFrequency: "monthly" as const,
    priority: 0.6,
  }));

  return [...staticPages, ...servicePages, ...blogPages];
}
