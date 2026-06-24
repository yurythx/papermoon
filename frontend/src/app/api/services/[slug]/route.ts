import { NextRequest, NextResponse } from "next/server";

const DJANGO_URL =
  process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

type Context = { params: Promise<{ slug: string }> };

/**
 * GET /api/services/{slug}
 *
 * Public BFF route — no auth required.
 * Proxies to Django CMS endpoint and returns the full service page content.
 * Returns null (200) when the slug has no CMS data yet (frontend falls back to
 * static services-content.ts).
 */
export async function GET(
  _req: NextRequest,
  { params }: Context
): Promise<NextResponse> {
  const { slug } = await params;

  try {
    const res = await fetch(`${DJANGO_URL}/cms/services/${slug}/`, {
      // ISR: Next.js caches this fetch result and revalidates every 60s
      next: { revalidate: 60, tags: [`service-page-${slug}`] },
    });

    if (res.status === 404) {
      return NextResponse.json(null, { status: 200 });
    }

    if (!res.ok) {
      return NextResponse.json(null, { status: 200 });
    }

    const data = await res.json();
    // Unwrap Django unified response envelope { success, data, error }
    const payload = data?.data ?? data;
    return NextResponse.json(payload);
  } catch {
    // Django offline → return null so the frontend falls back to static data
    return NextResponse.json(null, { status: 200 });
  }
}
