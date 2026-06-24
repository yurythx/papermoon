import { NextRequest, NextResponse } from "next/server";
import { applyAuthCookies, djangoFetch } from "@/lib/session";

export async function POST(req: NextRequest) {
  const body = await req.json();

  const django = await djangoFetch("/auth/login/", {
    method: "POST",
    body: JSON.stringify(body),
  });

  const payload = await django.json();

  if (!django.ok || !payload.success) {
    return NextResponse.json(payload, { status: django.status });
  }

  const { access, refresh } = payload.data as { access: string; refresh: string };

  const response = NextResponse.json({ success: true, data: { message: "ok" }, error: null });
  applyAuthCookies(response, access, refresh);
  return response;
}
