"use client";

import { memo, useState, useRef, useEffect } from "react";
import { Menu, Bell, ChevronDown, LogOut, User, Building2, CheckCheck } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { useSidebarStore } from "@/store/sidebar";
import { authService, notificationService } from "@/lib/services";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import type { MeResponse } from "@/types";

/* ── NotificationBellMenu ───────────────────────────────────────────── */

const NotificationBellMenu = memo(function NotificationBellMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { me } = useAuthStore();

  const { data } = useQuery({
    queryKey: ["notifications-bell"],
    queryFn: () => notificationService.list(),
    refetchInterval: 30_000,
    enabled: !!me?.customer,
  });

  const markAllMutation = useMutation({
    mutationFn: () => notificationService.markAllRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications-bell"] }),
  });

  const markOneMutation = useMutation({
    mutationFn: (id: string) => notificationService.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications-bell"] }),
  });

  const unread = data?.unread_count ?? 0;

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (!open) return;

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={`Notificações${unread > 0 ? ` — ${unread} não lidas` : ""}`}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-controls="topbar-notifications-menu"
        className="relative p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-1"
      >
        <Bell size={17} />
        {unread > 0 && (
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-accent border border-surface-1" />
        )}
      </button>

      {open && (
        <div
          id="topbar-notifications-menu"
          role="menu"
          aria-label="Notificações"
          className="absolute right-0 top-full mt-2 w-80 bg-surface-2 border border-border-default rounded-xl shadow-lg z-50 animate-slide-up overflow-hidden"
        >
          <div className="px-4 py-3 border-b border-border-subtle flex items-center justify-between">
            <span className="text-sm font-semibold text-text-primary">Notificações</span>
            {unread > 0 && (
              <button
                type="button"
                onClick={() => markAllMutation.mutate()}
                disabled={markAllMutation.isPending}
                className="flex items-center gap-1 rounded-sm text-xs text-brand-accent hover:underline disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-2"
                title="Marcar todas como lidas"
              >
                <CheckCheck size={12} />
                Marcar todas
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {!data?.results?.length ? (
              <div className="px-4 py-8 text-center text-sm text-text-tertiary">
                Nenhuma notificação
              </div>
            ) : (
              data.results.slice(0, 5).map((n) => (
                <button
                  key={n.id}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    if (!n.is_read) {
                      markOneMutation.mutate(n.id);
                    }
                  }}
                  className={cn(
                    "block w-full px-4 py-3 border-b border-border-subtle last:border-0 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-border-focus",
                    !n.is_read ? "bg-brand-accent/5 hover:bg-brand-accent/10 cursor-pointer" : "hover:bg-surface-3"
                  )}
                >
                  <div className="flex items-start gap-2">
                    {!n.is_read && (
                      <span className="w-1.5 h-1.5 rounded-full bg-brand-accent mt-1.5 shrink-0" />
                    )}
                    <div className={cn(!n.is_read ? "" : "pl-3.5")}>
                      <p className="text-sm font-medium text-text-primary">{n.subject}</p>
                      <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">{n.body}</p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>

          <div className="px-4 py-2.5 border-t border-border-subtle">
            <Link
              href="/dashboard/notifications"
              onClick={() => setOpen(false)}
              className="rounded-sm text-xs text-brand-accent hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-2"
              role="menuitem"
            >
              Ver todas as notificações →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
});

/* ── UserMenu ───────────────────────────────────────────────────────── */

interface UserMenuProps {
  me: MeResponse | null;
  onLogout: () => void;
}

const UserMenu = memo(function UserMenu({ me, onLogout }: UserMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (!open) return;

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [open]);

  const initials = me?.user?.email?.slice(0, 2).toUpperCase() ?? "??";

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label="Abrir menu do usuário"
        aria-expanded={open}
        aria-haspopup="menu"
        aria-controls="topbar-user-menu"
        className="flex items-center gap-2 p-1.5 rounded-md hover:bg-surface-3 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-1"
      >
        <div className="w-7 h-7 rounded-full bg-brand-accent/20 border border-brand-accent/30 flex items-center justify-center">
          <span className="text-xs font-semibold text-brand-accent">{initials}</span>
        </div>
        <ChevronDown size={13} className="text-text-tertiary hidden sm:block" />
      </button>

      {open && (
        <div
          id="topbar-user-menu"
          role="menu"
          aria-label="Menu do usuário"
          className="absolute right-0 top-full mt-2 w-56 bg-surface-2 border border-border-default rounded-xl shadow-lg z-50 animate-slide-up overflow-hidden"
        >
          <div className="px-4 py-3 border-b border-border-subtle">
            <p className="text-sm font-medium text-text-primary truncate">{me?.user?.email}</p>
            <p className="text-xs text-text-tertiary capitalize mt-0.5">{me?.role ?? "membro"}</p>
          </div>

          <div className="py-1">
            <Link
              href="/dashboard/profile"
              onClick={() => setOpen(false)}
              role="menuitem"
              className="flex items-center gap-2.5 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-border-focus"
            >
              <User size={15} />
              Minha empresa
            </Link>
          </div>

          <div className="py-1 border-t border-border-subtle">
            <button
              type="button"
              onClick={() => { setOpen(false); onLogout(); }}
              role="menuitem"
              className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-text-secondary hover:text-danger hover:bg-danger-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-border-focus"
            >
              <LogOut size={15} />
              Sair
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

/* ── Topbar ─────────────────────────────────────────────────────────── */

export function Topbar() {
  const { me, clearMe } = useAuthStore();
  const { toggle, toggleMobile } = useSidebarStore();
  const router = useRouter();

  function handleLogout() {
    authService.logout().finally(() => {
      clearMe();
      router.push("/login");
    });
  }

  function handleMenuToggle() {
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      toggleMobile();
    } else {
      toggle();
    }
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-14 bg-surface-1 border-b border-border-subtle flex items-center px-4 gap-3">
      <button
        type="button"
        onClick={handleMenuToggle}
        aria-label="Alternar menu lateral"
        className="p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-1"
      >
        <Menu size={18} />
      </button>

      <div className="flex items-center gap-2 mr-4">
        <PaperMoonMark idSuffix="topbar" glow />
        <span className="text-sm font-semibold text-text-primary hidden sm:block tracking-tight">
          PaperMoon
        </span>
      </div>

      {me?.customer && (
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-2 border border-border-subtle">
          <Building2 size={13} className="text-text-tertiary shrink-0" />
          <span className="text-sm text-text-primary font-medium max-w-[160px] truncate">
            {me.customer.company_name}
          </span>
          {me.customer.status === "suspended" && (
            <span className="w-1.5 h-1.5 rounded-full bg-danger shrink-0" />
          )}
        </div>
      )}

      <div className="flex-1" />

      <ThemeToggle />
      <NotificationBellMenu />
      <UserMenu me={me} onLogout={handleLogout} />
    </header>
  );
}
