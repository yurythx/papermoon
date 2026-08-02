import { NextRequest, NextResponse } from "next/server";
import { djangoFetch } from "@/lib/session";

// No cookies/headers/searchParams read here, so Next.js would otherwise treat this
// as a static route candidate and try to prerender it at build time — with no Django
// reachable during `docker build`, that fails the whole build. Force dynamic: this
// must always hit Django live anyway (it reflects mutable DB-backed SSO config).
export const dynamic = "force-dynamic";

// Kicks off staff SSO. Resolves the Keycloak authorize URL server-side (Django owns
// state/PKCE/nonce — see docs/adrs/0002-sso-keycloak-staff.md) and only then redirects
// the browser, keeping the BFF as the sole point of contact for the client.
export async function GET(req: NextRequest) {
  const django = await djangoFetch("/auth/sso/login/");
  const payload = await django.json();

  if (!django.ok || !payload.success || !payload.data?.authorize_url) {
    return NextResponse.redirect(new URL("/login?error=sso_unavailable", req.url));
  }

  return NextResponse.redirect(payload.data.authorize_url as string);
}
