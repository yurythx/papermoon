import { NextRequest, NextResponse } from "next/server";
import { applyAuthCookies, djangoFetch } from "@/lib/session";

// This is the redirect_uri registered with the Keycloak client — the only URL the
// Keycloak side of the flow ever talks to. Django never receives the browser
// redirect directly (see docs/adrs/0002-sso-keycloak-staff.md).
export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;

  if (params.get("error")) {
    return NextResponse.redirect(new URL("/login?error=sso_failed", req.url));
  }

  const code = params.get("code");
  const state = params.get("state");
  if (!code || !state) {
    return NextResponse.redirect(new URL("/login?error=sso_failed", req.url));
  }

  const django = await djangoFetch("/auth/sso/callback/", {
    method: "POST",
    body: JSON.stringify({ code, state }),
  });
  const payload = await django.json();

  if (!django.ok || !payload.success) {
    return NextResponse.redirect(new URL("/login?error=sso_failed", req.url));
  }

  const { access, refresh } = payload.data as { access: string; refresh: string };
  const response = NextResponse.redirect(new URL("/backoffice", req.url));
  applyAuthCookies(response, access, refresh);
  return response;
}
