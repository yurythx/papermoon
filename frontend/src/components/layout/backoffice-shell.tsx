"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useSidebarStore } from "@/store/sidebar";
import { authService } from "@/lib/services";
import { cn } from "@/lib/utils";
import { Topbar } from "@/components/layout/topbar";
import { Sidebar } from "@/components/layout/sidebar";
import { Spinner } from "@/components/ui/spinner";

export function BackofficeShell({ children }: { children: React.ReactNode }) {
  const { me, setMe, clearMe } = useAuthStore();
  const { isOpen } = useSidebarStore();
  const router = useRouter();
  const [loading, setLoading] = useState(!me);

  useEffect(() => {
    if (me) {
      setLoading(false);
      if (!me.user.is_staff) router.replace("/onboarding");
      return;
    }
    authService
      .me()
      .then((profile) => {
        setMe(profile);
        setLoading(false);
        if (!profile.user.is_staff) router.replace("/onboarding");
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
        <div className="px-4 py-4 md:px-8 md:py-6 max-w-[1600px] mx-auto animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
