"use client";

import { useEffect } from "react";
import Link from "next/link";
import * as Sentry from "@sentry/nextjs";
import { Button } from "@/components/ui/button";
import { RefreshCw, LayoutDashboard, AlertTriangle } from "lucide-react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function BackofficeError({ error, reset }: ErrorProps) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6 px-4">
      <div className="w-14 h-14 rounded-2xl bg-danger-muted border border-danger/20 flex items-center justify-center">
        <AlertTriangle size={24} className="text-danger" />
      </div>

      <div className="space-y-2 max-w-sm">
        <h2 className="text-xl font-bold text-text-primary">Erro no backoffice</h2>
        <p className="text-sm text-text-secondary leading-relaxed">
          Esta seção encontrou um problema. Tente recarregar ou volte ao painel principal.
        </p>
        {error.digest && (
          <p className="text-xs text-text-tertiary font-mono pt-1">Código: {error.digest}</p>
        )}
      </div>

      <div className="flex gap-3">
        <Button variant="primary" size="sm" onClick={reset}>
          <RefreshCw size={13} className="mr-1.5" />
          Recarregar
        </Button>
        <Link href="/backoffice">
          <Button variant="secondary" size="sm">
            <LayoutDashboard size={13} className="mr-1.5" />
            Início
          </Button>
        </Link>
      </div>
    </div>
  );
}
