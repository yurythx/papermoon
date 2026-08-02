import { NextResponse } from "next/server";
import { djangoFetch } from "@/lib/session";

// No cookies/headers/searchParams read here, so force dynamic (see app/api/auth/sso/route.ts
// for why) — this must also never be statically cached, it reflects live DB config.
export const dynamic = "force-dynamic";

// Public — the login page polls this on mount to decide whether to show the
// "Entrar com Keycloak" button. Backed by SSOConfiguration (DB), editable at
// runtime in Backoffice → Configurações — no env var, no redeploy needed.
export async function GET() {
  try {
    const django = await djangoFetch("/auth/sso/status/");
    const payload = await django.json();
    if (!django.ok || !payload.success) {
      return NextResponse.json({ success: true, data: { enabled: false }, error: null });
    }
    return NextResponse.json(payload);
  } catch {
    // Django unreachable — fail closed (hide the button) rather than error the login page.
    return NextResponse.json({ success: true, data: { enabled: false }, error: null });
  }
}
