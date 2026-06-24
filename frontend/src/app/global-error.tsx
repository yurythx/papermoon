"use client";

import { useEffect } from "react";
import * as Sentry from "@sentry/nextjs";
import { RefreshCw } from "lucide-react";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

// Wraps the root layout — must include <html> and <body>.
// Kept minimal on purpose: at this level the design system may not be available
// (fonts, CSS vars, etc. may have failed to load), so we use only inline styles.
export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="pt-BR">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "rgb(15 23 42)", color: "rgb(248 250 252)", display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div style={{ textAlign: "center", maxWidth: 400, padding: "32px 24px", border: "1px solid rgba(248, 250, 252, 0.12)", borderRadius: 20, background: "rgba(15, 23, 42, 0.72)", boxShadow: "0 20px 60px rgba(15, 23, 42, 0.45)" }}>
          <p style={{ fontSize: 72, fontWeight: 900, margin: "0 0 16px", color: "rgb(251 191 36)" }}>500</p>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>Erro crítico</h1>
          <p style={{ fontSize: 14, color: "rgba(203, 213, 225, 0.92)", lineHeight: 1.6, margin: "0 0 24px" }}>
            Ocorreu um erro que impediu o carregamento da aplicação.
            Nossa equipe foi notificada.
          </p>
          {error.digest && (
            <p style={{ fontSize: 11, color: "rgba(148, 163, 184, 0.9)", fontFamily: "monospace", margin: "0 0 24px" }}>
              Código: {error.digest}
            </p>
          )}
          <button
            onClick={reset}
            style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "rgb(251 191 36)", color: "rgb(15 23 42)", border: "none", borderRadius: 10, padding: "10px 20px", fontSize: 14, fontWeight: 700, cursor: "pointer" }}
          >
            <RefreshCw size={14} />
            Tentar novamente
          </button>
        </div>
      </body>
    </html>
  );
}
