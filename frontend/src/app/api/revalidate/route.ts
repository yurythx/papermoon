import { revalidatePath, revalidateTag } from "next/cache";
import { NextRequest, NextResponse } from "next/server";

/**
 * POST /api/revalidate
 *
 * Called by the Django Celery task (apps.cms.tasks.revalidate_service_page)
 * after a ServicePage is saved in the admin.
 *
 * Body: { "secret": "<REVALIDATE_SECRET>", "slug": "<service-slug>" }
 *
 * Purges ISR cache for /servicos/{slug} immediately instead of waiting
 * for the 60s revalidate window.
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

  return NextResponse.json({ revalidated: true, slug });
}
