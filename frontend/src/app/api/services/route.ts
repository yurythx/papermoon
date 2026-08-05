import { NextResponse } from "next/server";

import { SERVICES } from "@/lib/services-content";
import { fetchActiveServiceSlugs, isServiceVisible } from "@/lib/active-services";

const DJANGO_URL =
  process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

const STATIC_SLUGS = SERVICES.map((s) => s.slug);

/**
 * GET /api/services
 *
 * Returns the list of service slugs, merging CMS slugs with static slugs,
 * minus any product currently marked unavailable (Product.is_active=False)
 * — this is what generateStaticParams uses, so a disabled service simply
 * never gets a static /servicos/<slug> page built for it.
 */
export async function GET(): Promise<NextResponse> {
  const activeSlugs = await fetchActiveServiceSlugs();

  try {
    const res = await fetch(`${DJANGO_URL}/cms/services/`, {
      next: { revalidate: 300 },
    });

    let allSlugs = STATIC_SLUGS;
    if (res.ok) {
      const data = await res.json();
      const payload: string[] = data?.data ?? data ?? [];
      const cmsSlugs: string[] = Array.isArray(payload) ? payload : [];
      allSlugs = Array.from(new Set([...STATIC_SLUGS, ...cmsSlugs]));
    }

    return NextResponse.json(allSlugs.filter((s) => isServiceVisible(s, activeSlugs)));
  } catch {
    return NextResponse.json(STATIC_SLUGS.filter((s) => isServiceVisible(s, activeSlugs)));
  }
}
