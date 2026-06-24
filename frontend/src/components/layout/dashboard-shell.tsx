"use client";

import { memo, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useSidebarStore } from "@/store/sidebar";
import { authService } from "@/lib/services";
import { cn } from "@/lib/utils";
import { Topbar } from "@/components/layout/topbar";
import { Sidebar } from "@/components/layout/sidebar";
import { Spinner } from "@/components/ui/spinner";
import { AlertTriangle, XCircle } from "lucide-react";

const SuspendedBanner = memo(function SuspendedBanner() {
  return (
    <div className="bg-danger-muted border-b border-danger/20 px-6 py-3 flex items-center gap-3">
      <AlertTriangle size={16} className="text-danger shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-semibold text-danger">Conta suspensa</p>
        <p className="text-xs text-text-secondary mt-0.5">
          Sua conta está temporariamente suspensa. Regularize os pagamentos pendentes para reativar o acesso.
        </p>
      </div>
      <a
        href="/dashboard/invoices"
        className="text-xs font-semibold text-slate-950 bg-brand-accent border border-brand-accent/80 px-3 py-1.5 rounded-md hover:bg-brand-accent/90 transition-colors shrink-0"
      >
        Ver faturas
      </a>
    </div>
  );
});

const CancelledBanner = memo(function CancelledBanner() {
  return (
    <div className="bg-surface-2 border-b border-border-subtle px-6 py-3 flex items-center gap-3">
      <XCircle size={16} className="text-text-tertiary shrink-0" />
      <div className="flex-1">
        <p className="text-sm font-medium text-text-secondary">
          Esta conta está cancelada e em modo somente leitura.
        </p>
      </div>
    </div>
  );
});

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { me, setMe, clearMe } = useAuthStore();
  const { isOpen } = useSidebarStore();
  const router = useRouter();
  const [loading, setLoading] = useState(!me);

  useEffect(() => {
    if (me) {
      setLoading(false);
      if (!me.customer) router.replace("/onboarding");
      return;
    }
    authService
      .me()
      .then((profile) => {
        setMe(profile);
        setLoading(false);
        if (!profile.customer) router.replace("/onboarding");
      })
      .catch(() => {
        clearMe();
        router.replace("/login");
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-0">
        <Spinner size="lg" />
      </div>
    );
  }

  const status = me?.customer?.status;

  return (
    <div className="min-h-screen bg-surface-0">
      <Topbar />
      <Sidebar />

      <main
        className={cn(
          "pt-14 min-h-screen transition-all duration-200 ease-smooth",
          isOpen ? "md:ml-60" : "md:ml-16"
        )}
      >
        {status === "suspended" && <SuspendedBanner />}
        {status === "cancelled" && <CancelledBanner />}

        <div className="px-4 py-4 md:px-8 md:py-6 max-w-[1600px] mx-auto animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
