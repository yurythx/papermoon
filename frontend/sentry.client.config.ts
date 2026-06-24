import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  enabled: process.env.NODE_ENV === "production",
  tracesSampleRate: 0.05,
  // Only send errors, not performance data from the client by default
  replaysOnErrorSampleRate: 1.0,
  replaysSessionSampleRate: 0,
});
