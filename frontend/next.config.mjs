import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const isProduction = process.env.NODE_ENV === "production";

const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "www.chatwoot.com" },
      { protocol: "https", hostname: "n8niostorageaccount.blob.core.windows.net" },
      // Django media files — dev (local) e Docker-internal
      { protocol: "http", hostname: "localhost", port: "8000" },
      { protocol: "http", hostname: "django-api", port: "8000" },
      // Produção real (deployment.md): papermoon.cloud, atrás do Cloudflare
      // Tunnel — papermoon.com.br abaixo é um domínio ainda não usado no ar,
      // mantido por segurança caso vire o domínio real no futuro.
      { protocol: "https", hostname: "papermoon.cloud" },
      { protocol: "https", hostname: "**.papermoon.cloud" },
      { protocol: "https", hostname: "**.papermoon.com.br" },
    ],
  },
  // MEDIA_URL do Django (settings.MEDIA_URL="/media/") não tem hostname público
  // próprio — o Cloudflare Tunnel só aponta pro Next.js (app.papermoon.cloud →
  // nextjs:3000, ver deployment.md), então build_public_media_url() no backend
  // (shared/public_urls.py) precisa de um MEDIA_PUBLIC_BASE_URL apontando pra
  // cá, e esse rewrite fecha o outro lado: proxya /media/* pro django-api
  // internamente, sem precisar de uma rota nova no painel do Cloudflare.
  //
  // Hostname fixo de propósito, não `process.env.DJANGO_INTERNAL_URL` — com
  // output: "standalone", rewrites() é resolvido durante `next build` (dentro
  // do estágio builder do Dockerfile), onde DJANGO_INTERNAL_URL não existe
  // (é secret só de runtime, injetado pelo docker-compose ao subir o
  // container). Ler o env aqui congelava sempre o fallback "localhost:8000" —
  // confirmado ao vivo: ECONNREFUSED ::1:8000 dentro do container do Next.js.
  // "django-api" é o nome do serviço no Compose, fixo entre ambientes onde
  // esse rewrite de fato importa (produção — localmente MEDIA_PUBLIC_BASE_URL
  // não é setado, então essa rota nunca é exercitada).
  async rewrites() {
    return [{ source: "/media/:path*", destination: "http://django-api:8000/media/:path*" }];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          // middleware.ts sets the real per-request CSP in production (no
          // nonce — ver o motivo lá). Este aqui é só o fallback estático,
          // usado quando o middleware é pulado (dev mode, static export).
          // Mantenha os dois img-src em sincronia — já divergiram uma vez
          // (host do Chatwoot/n8n faltando aqui) sem quebrar nada na hora
          // só porque essas imagens passam por next/image (mesma origem);
          // qualquer <img> direto pegaria a CSP errada silenciosamente.
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              `script-src 'self' 'unsafe-inline'${isProduction ? "" : " 'unsafe-eval'"}`,
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: http://localhost:8000 http://django-api:8000 https://papermoon.cloud https://*.papermoon.cloud https://*.papermoon.com.br https://www.chatwoot.com https://n8niostorageaccount.blob.core.windows.net",
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
