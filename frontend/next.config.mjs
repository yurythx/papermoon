import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const isProduction = process.env.NODE_ENV === "production";

const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "www.chatwoot.com" },
      { protocol: "https", hostname: "n8niostorageaccount.blob.core.windows.net" },
      // Django media files — dev (local) and Docker-internal
      { protocol: "http", hostname: "localhost", port: "8000" },
      { protocol: "http", hostname: "django-api", port: "8000" },
      // Production: any papermoon.com.br subdomain serving media
      { protocol: "https", hostname: "**.papermoon.com.br" },
    ],
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          // CSP is enforced by middleware in production (nonce-based, per-request).
          // This static fallback covers dev mode and static export where middleware skips.
          // Middleware sets CSP per-request in production.
          // This static fallback applies only when middleware is bypassed (e.g. static export).
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              `script-src 'self' 'unsafe-inline'${isProduction ? "" : " 'unsafe-eval'"}`,
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: https://www.chatwoot.com https://n8niostorageaccount.blob.core.windows.net",
              "connect-src 'self' https://*.sentry.io",
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
            ].join("; "),
          },
          ...(isProduction
            ? [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" }]
            : []),
        ],
      },
    ];
  },
};

const hasSentry = Boolean(process.env.NEXT_PUBLIC_SENTRY_DSN);

// withSentryConfig is skipped when DSN is absent (local dev, CI without secrets)
// so the build never fails due to missing SENTRY_ORG / SENTRY_PROJECT.
export default hasSentry
  ? withSentryConfig(nextConfig, {
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      silent: true,
      sourcemaps: { disable: false },
      autoInstrumentServerFunctions: false,
      autoInstrumentMiddleware: false,
    })
  : nextConfig;
