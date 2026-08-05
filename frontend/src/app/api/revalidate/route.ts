import { revalidatePath, revalidateTag } from "next/cache";
import { NextRequest, NextResponse } from "next/server";

/**
 * POST /api/revalidate
 *
 * Called by the Django Celery task (apps.cms.tasks.revalidate_service_page)
 * after a ServicePage is saved OR a Product's is_active flag changes.
 *
 * Body: { "secret": "<REVALIDATE_SECRET>", "slug": "<service-slug>" }
 *
 * Purges ISR cache for /servicos/{slug} immediately instead of waiting for
 * the 60s revalidate window. Also purges "/" and "/servicos" — both source
 * their service grids from the same active/inactive signal (see
 * lib/active-services.ts), so a just-toggled service could otherwise sit
 * there stale until its own next visit (stale-while-revalidate only
 * refreshes on the NEXT request to that exact path, which may never come
 * for a low-traffic listing).
 */
export async function POST(req: NextRequest): Promise<NextResponse> {
  const secret = process.env.REVALIDATE_SECRET;
  if (!secret) {
    return NextResponse.json({ error: "not_configured" }, { status: 503 });
  }

  let body: { secret?: string; slug?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid_json" }, { status: 400 });
  }

  if (body.secret !== secret) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }

  const slug = body.slug?.trim();
  if (!slug) {
    return NextResponse.json({ error: "missing_slug" }, { status: 400 });
  }

  revalidatePath(`/servicos/${slug}`);
  revalidateTag(`service-page-${slug}`);
  revalidatePath("/servicos");
  revalidatePath("/");
  revalidateTag("active-services");

  return NextResponse.json({ revalidated: true, slug });
}
