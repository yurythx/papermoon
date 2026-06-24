"use client";

import { useEffect } from "react";
import Link from "next/link";
import * as Sentry from "@sentry/nextjs";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { Button } from "@/components/ui/button";
import { RefreshCw, Home, AlertTriangle } from "lucide-react";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-0 px-6">
      <div className="max-w-md w-full text-center space-y-8">
        {/* Logo */}
        <div className="flex justify-center">
          <div className="flex items-center gap-2.5">
            <PaperMoonMark idSuffix="error" size={32} />
            <span className="text-lg font-bold text-text-primary">PaperMoon</span>
          </div>
        </div>

        {/* Error icon */}
        <div className="flex justify-center">
          <div className="w-16 h-16 rounded-2xl bg-danger-muted border border-danger/20 flex items-center justify-center">
            <AlertTriangle size={28} className="text-danger" />
          </div>
        </div>

        {/* Message */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-text-primary">Algo deu errado</h1>
          <p className="text-sm text-text-secondary leading-relaxed">
            Ocorreu um erro inesperado. Nossa equipe já foi notificada.
            Tente recarregar a página ou volte ao início.
          </p>
        </div>

        {/* Error digest for support */}
        {error.digest && (
          <div className="bg-surface-1 border border-border-subtle rounded-lg px-4 py-2 text-center">
            <p className="text-xs text-text-tertiary font-mono">
              Código: {error.digest}
            </p>
          </div>
        )}

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button variant="primary" size="md" onClick={reset}>
            <RefreshCw size={14} className="mr-1.5" />
            Tentar novamente
          </Button>
          <Link href="/dashboard">
            <Button variant="secondary" size="md">
              <Home size={14} className="mr-1.5" />
              Ir para o dashboard
            </Button>
          </Link>
        </div>

        <p className="text-xs text-text-tertiary">
          Precisa de ajuda?{" "}
          <a href="mailto:suporte@papermoon.com.br" className="underline hover:text-text-secondary transition-colors">
            suporte@papermoon.com.br
          </a>
        </p>
      </div>
    </div>
  );
}
