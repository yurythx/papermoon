import { NextResponse } from "next/server";

import { SERVICES } from "@/lib/services-content";

const DJANGO_URL =
  process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

const STATIC_SLUGS = SERVICES.map((s) => s.slug);

/**
 * GET /api/services
 *
 * Returns the list of service slugs, merging CMS slugs with static slugs.
 * Used by generateStaticParams to pre-render all service pages at build time.
 */
export async function GET(): Promise<NextResponse> {
  try {
    const res = await fetch(`${DJANGO_URL}/cms/services/`, {
      next: { revalidate: 300 },
    });

    if (!res.ok) {
      return NextResponse.json(STATIC_SLUGS);
    }

    const data = await res.json();
    const payload: string[] = data?.data ?? data ?? [];
    const cmsSlugs: string[] = Array.isArray(payload) ? payload : [];
    const seen = new Set<string>(STATIC_SLUGS);
    for (const s of cmsSlugs) seen.add(s);
    return NextResponse.json(Array.from(seen));
  } catch {
    return NextResponse.json(STATIC_SLUGS);
  }
}
