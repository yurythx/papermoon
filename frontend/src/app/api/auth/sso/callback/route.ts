import { NextRequest, NextResponse } from "next/server";
import { applyAuthCookies, djangoFetch } from "@/lib/session";

// Base para os redirects deste handler. NÃO usar `req.url`: em standalone mode
// com HOSTNAME=0.0.0.0 (obrigatório pro bind do Docker), o Next.js reflete esse
// bind address no `req.url`/`req.nextUrl` em vez do Host real da requisição —
// resultava em redirect pra "http://0.0.0.0:3000/...", inacessível no navegador.
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

// This is the redirect_uri registered with the Keycloak client — the only URL the
// Keycloak side of the flow ever talks to. Django never receives the browser
// redirect directly (see docs/adrs/0002-sso-keycloak-staff.md).
export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;

  if (params.get("error")) {
    return NextResponse.redirect(new URL("/login?error=sso_failed", SITE_URL));
  }

  const code = params.get("code");
  const state = params.get("state");
  if (!code || !state) {
    return NextResponse.redirect(new URL("/login?error=sso_failed", SITE_URL));
  }

  const django = await djangoFetch("/auth/sso/callback/", {
    method: "POST",
    body: JSON.stringify({ code, state }),
  });
  const payload = await django.json();

  if (!django.ok || !payload.success) {
    return NextResponse.redirect(new URL("/login?error=sso_failed", SITE_URL));
  }

  const { access, refresh } = payload.data as { access: string; refresh: string };
  const response = NextResponse.redirect(new URL("/backoffice", SITE_URL));
  applyAuthCookies(response, access, refresh);
  return response;
}
