import { revalidatePath, revalidateTag } from "next/cache";
import { NextRequest, NextResponse } from "next/server";

/**
 * POST /api/revalidate
 *
 * Called by Django Celery tasks after content changes:
 * - apps.cms.tasks.revalidate_service_page (ServicePage saved, or a
 *   Product's is_active flag changes) — type "service" (default, omitted
 *   by the CMS task for backward compatibility).
 * - apps.blog.tasks.revalidate_blog_post (BlogPost saved) — type "blog".
 *
 * Body: { "secret": "<REVALIDATE_SECRET>", "slug": "<slug>", "type"?: "service" | "blog" }
 *
 * Purges ISR cache immediately instead of waiting for the 60s revalidate
 * window. Also purges the listing/home paths that source their grids from
 * the same signal — a just-toggled service or just-published post could
 * otherwise sit stale until its own next visit (stale-while-revalidate only
 * refreshes on the NEXT request to that exact path, which may never come
 * for a low-traffic listing).
 */
export async function POST(req: NextRequest): Promise<NextResponse> {
  const secret = process.env.REVALIDATE_SECRET;
  if (!secret) {
    return NextResponse.json({ error: "not_configured" }, { status: 503 });
  }

  let body: { secret?: string; slug?: string; type?: "service" | "blog" };
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

  if (body.type === "blog") {
    revalidatePath(`/blog/${slug}`);
    revalidateTag(`blog-post-${slug}`);
    revalidatePath("/blog");
    revalidateTag("blog-posts");
  } else {
    revalidatePath(`/servicos/${slug}`);
    revalidateTag(`service-page-${slug}`);
    revalidatePath("/servicos");
    revalidatePath("/");
    revalidateTag("active-services");
  }

  return NextResponse.json({ revalidated: true, slug, type: body.type ?? "service" });
}
