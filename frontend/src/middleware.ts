import { NextResponse } from "next/server";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function middleware() {
  const isProduction = process.env.NODE_ENV === "production";

  // CSP note: nonce-based CSP is incompatible with Next.js App Router out of the box.
  // The browser spec says 'unsafe-inline' is IGNORED whenever a nonce is present in
  // script-src — so Next.js's own inline hydration scripts and next-themes's theme-init
  // script get blocked, causing React hydration failures (error #423).
  //
  // Correct approach for this stack: no nonce, use 'self' + 'unsafe-inline'.
  // Scripts from /_next/static/ are same-origin ('self') and inline scripts are
  // allowed by 'unsafe-inline'. XSS is still meaningfully limited by default-src,
  // frame-ancestors, form-action, and base-uri.
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'unsafe-inline'${isProduction ? "" : " 'unsafe-eval'"}`,
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: blob:",
    "connect-src 'self' https://*.sentry.io",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join("; ");

  const response = NextResponse.next();
  response.headers.set("Content-Security-Policy", csp);
  return response;
}

export const config = {
  matcher: [
    // Apply to all routes except Next.js static assets and image optimization
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
