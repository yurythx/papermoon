"use client";

import { memo, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Key,
  ShoppingBag,
  CreditCard,
  Users,
  Bell,
  Settings,
  Building2,
  BarChart3,
  Shield,
  FileText,
  Package,
  Fingerprint,
  Activity,
  ChevronUp,
  FileEdit,
} from "lucide-react";
import { useSidebarStore } from "@/store/sidebar";
import { useAuthStore } from "@/store/auth";
import { useQuery } from "@tanstack/react-query";
import { licenseService, invoiceService, notificationService, subscriptionService, adminService } from "@/lib/services";
import type { Subscription } from "@/types";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  exact?: boolean;
}

const CLIENT_NAV: { section: string; items: NavItem[] }[] = [
  {
    section: "Visão Geral",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, exact: true },
    ],
  },
  {
    section: "Serviços",
    items: [
      { href: "/dashboard/licenses", label: "Minhas Licenças", icon: Key },
      { href: "/dashboard/subscriptions", label: "Meus Contratos", icon: Package },
      { href: "/dashboard/catalog", label: "Nossos Serviços", icon: ShoppingBag },
      { href: "/dashboard/api-keys", label: "API Keys", icon: Fingerprint },
    ],
  },
  {
    section: "Financeiro",
    items: [
      { href: "/dashboard/invoices", label: "Faturas", icon: CreditCard },
    ],
  },
  {
    section: "Equipe",
    items: [
      { href: "/dashboard/team", label: "Membros & Assentos", icon: Users },
      { href: "/dashboard/notifications", label: "Notificações", icon: Bell },
    ],
  },
  {
    section: "Conta",
    items: [
      { href: "/dashboard/profile", label: "Minha empresa", icon: Settings },
    ],
  },
];

const ADMIN_NAV: { section: string; items: NavItem[] }[] = [
  {
    section: "Visão Geral",
    items: [
      { href: "/backoffice", label: "Métricas", icon: BarChart3, exact: true },
    ],
  },
  {
    section: "Operações",
    items: [
      { href: "/backoffice/customers", label: "Clientes", icon: Building2 },
      { href: "/backoffice/subscriptions", label: "Serviços", icon: Package },
      { href: "/backoffice/invoices", label: "Faturas", icon: FileText },
    ],
  },
  {
    section: "Catálogo",
    items: [
      { href: "/backoffice/products", label: "Produtos", icon: ShoppingBag },
    ],
  },
  {
    section: "Conteúdo",
    items: [
      { href: "/backoffice/cms", label: "Páginas de Serviço", icon: FileEdit },
    ],
  },
  {
    section: "Sistema",
    items: [
      { href: "/backoffice/audit", label: "Auditoria", icon: Shield },
      { href: "/backoffice/health", label: "Status", icon: Activity },
    ],
  },
];

const ADMIN_NAV_FLAT = ADMIN_NAV.flatMap((g) => g.items);

const BADGE_COLORS = {
  warning: "bg-warning text-text-inverse",
  danger: "bg-danger text-white",
  info: "bg-info text-white",
} as const;

/* ── NavLink ────────────────────────────────────────────────────────── */

interface NavLinkProps {
  item: NavItem;
  active: boolean;
  collapsed: boolean;
  badgeLabel?: string;
  badgeVariant?: "warning" | "danger" | "info";
}

const NavLink = memo(function NavLink({ item, active, collapsed, badgeLabel, badgeVariant }: NavLinkProps) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      title={collapsed ? item.label : undefined}
      className={cn(
        "group flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150 mb-0.5",
        "relative overflow-hidden",
        active
          ? "bg-brand-accent/15 text-text-primary border border-brand-accent/25"
          : "text-text-secondary hover:text-text-primary hover:bg-surface-3",
        collapsed && "justify-center px-2"
      )}
    >
      <Icon
        size={16}
        className={cn(
          "shrink-0 transition-colors",
          active ? "text-brand-accent" : "text-text-tertiary group-hover:text-text-secondary"
        )}
      />

      {!collapsed && (
        <>
          <span className="flex-1 truncate">{item.label}</span>
          {badgeLabel && badgeVariant && (
            <span
              className={cn(
                "ml-auto text-xs font-bold px-1.5 py-0.5 rounded-full min-w-[18px] text-center",
                BADGE_COLORS[badgeVariant]
              )}
            >
              {badgeLabel}
            </span>
          )}
        </>
      )}

      {collapsed && badgeLabel && badgeVariant && (
        <span
          className={cn(
            "absolute top-1 right-1 w-2 h-2 rounded-full border border-surface-1",
            badgeVariant === "danger" && "bg-danger",
            badgeVariant === "warning" && "bg-warning",
            badgeVariant === "info" && "bg-info"
          )}
        />
      )}
    </Link>
  );
});

/* ── PlanWidget ─────────────────────────────────────────────────────── */

const CYCLE_LABEL: Record<string, string> = {
  monthly: "Mensal",
  yearly: "Anual",
  trial: "Trial",
  quarterly: "Trimestral",
};

interface PlanWidgetProps {
  customerStatus: string;
  subscription?: Subscription;
}

const PlanWidget = memo(function PlanWidget({ customerStatus, subscription }: PlanWidgetProps) {
  const isSuspended = customerStatus === "suspended";
  const isCancelled = customerStatus === "cancelled";

  const { pct, daysLeft } = (() => {
    if (!subscription?.starts_at || !subscription?.expires_at) return { pct: 0, daysLeft: 0 };
    const now = Date.now();
    const start = new Date(subscription.starts_at).getTime();
    const end = new Date(subscription.expires_at).getTime();
    const total = Math.max(1, end - start);
    return {
      pct: Math.min(100, Math.round((Math.max(0, now - start) / total) * 100)),
      daysLeft: Math.max(0, Math.ceil((end - now) / 86_400_000)),
    };
  })();

  const progressVariant: "default" | "warning" | "danger" =
    pct >= 90 ? "danger" : pct >= 70 ? "warning" : "default";

  return (
    <div className="p-3 border-t border-border-subtle">
      <div
        className={cn(
          "p-3 rounded-lg border",
          isSuspended ? "bg-danger-muted border-danger/25" : "bg-surface-2 border-border-subtle"
        )}
      >
        {isSuspended ? (
          <div className="flex items-start gap-2">
            <ChevronUp size={14} className="text-danger mt-0.5 shrink-0" />
            <div>
              <p className="text-xs font-semibold text-danger">Conta Suspensa</p>
              <p className="text-xs text-text-secondary mt-0.5">Regularize para reativar o acesso.</p>
            </div>
          </div>
        ) : isCancelled ? (
          <p className="text-xs font-semibold text-text-tertiary">Conta Cancelada</p>
        ) : subscription ? (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-xs font-semibold text-text-primary truncate max-w-[110px]">
                {subscription.product_name}
              </p>
              <span className="text-[10px] text-text-tertiary bg-surface-3 rounded px-1.5 py-0.5 shrink-0">
                {CYCLE_LABEL[subscription.billing_cycle] ?? subscription.billing_cycle}
              </span>
            </div>
            <Progress value={pct} variant={progressVariant} animated={pct >= 70} />
            <p className="text-[10px] text-text-tertiary mt-1.5">
              {daysLeft > 0
                ? `${daysLeft} dia${daysLeft !== 1 ? "s" : ""} restante${daysLeft !== 1 ? "s" : ""}`
                : "Expira hoje"}
            </p>
          </div>
        ) : (
          <div>
            <p className="text-xs font-semibold text-text-secondary mb-1">Nenhum contrato ativo</p>
            <a href="mailto:contato@papermoon.com.br" className="text-[10px] text-brand-accent hover:underline">
              Falar com a equipe →
            </a>
          </div>
        )}
      </div>
    </div>
  );
});

/* ── Sidebar ────────────────────────────────────────────────────────── */

export function Sidebar() {
  const { isOpen, mobileOpen, closeMobile } = useSidebarStore();
  const { me } = useAuthStore();
  const pathname = usePathname();

  useEffect(() => {
    closeMobile();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  const isAdmin = me?.user?.is_staff === true;
  const isBackoffice = pathname.startsWith("/backoffice");

  const { data: licenses } = useQuery({
    queryKey: ["licenses"],
    queryFn: licenseService.list,
    enabled: !!me?.customer && !isBackoffice,
    staleTime: 60_000,
  });

  const { data: invoices } = useQuery({
    queryKey: ["invoices-badge"],
    queryFn: () => invoiceService.list({ status: "overdue" }),
    enabled: !!me?.customer && !isBackoffice,
    staleTime: 60_000,
  });

  const { data: notifs } = useQuery({
    queryKey: ["notifications-bell"],
    queryFn: () => notificationService.list(),
    enabled: !!me?.customer,
    staleTime: 30_000,
  });

  const { data: subscriptions } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: subscriptionService.list,
    enabled: !!me?.customer && !isBackoffice,
    staleTime: 120_000,
  });

  const { data: pendingRegs = [] } = useQuery({
    queryKey: ["pending-registrations"],
    queryFn: adminService.listPendingRegistrations,
    enabled: isBackoffice && isAdmin,
    staleTime: 60_000,
    refetchInterval: 120_000,
  });

  const activeSub: Subscription | undefined =
    subscriptions?.results?.find((s) => s.status === "active" || s.status === "trial") ??
    subscriptions?.results?.[0];

  const expiringCount = licenses?.results?.filter(
    (l) => l.status === "active" && l.days_remaining <= 7
  ).length ?? 0;
  const overdueCount = invoices?.results?.length ?? 0;
  const unreadNotifs = notifs?.unread_count ?? 0;

  function isActive(href: string, exact?: boolean) {
    return exact ? pathname === href : pathname.startsWith(href);
  }

  const pendingCount = pendingRegs.length;

  function getBadge(href: string): { label: string; variant: "warning" | "danger" | "info" } | null {
    if (href === "/dashboard/licenses" && expiringCount > 0)
      return { label: String(expiringCount), variant: "warning" };
    if (href === "/dashboard/invoices" && overdueCount > 0)
      return { label: String(overdueCount), variant: "danger" };
    if (href === "/dashboard/notifications" && unreadNotifs > 0)
      return { label: String(unreadNotifs), variant: "info" };
    if (href === "/backoffice/customers" && pendingCount > 0)
      return { label: String(pendingCount), variant: "warning" };
    return null;
  }

  // On mobile, the sidebar is always full-width when open; only collapse on desktop when isOpen=false
  const collapsed = !isOpen && !mobileOpen;

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-14 bottom-0 z-40 flex flex-col bg-surface-1 border-r border-border-subtle",
          "transition-all duration-200 ease-smooth overflow-hidden",
          mobileOpen ? "translate-x-0 w-72" : "-translate-x-full w-72",
          "md:translate-x-0",
          isOpen ? "md:w-60" : "md:w-16"
        )}
      >
        <nav className="flex-1 overflow-y-auto overflow-x-hidden py-4 px-2">
          {isBackoffice ? (
            <>
              {ADMIN_NAV.map((group) => (
                <div key={group.section} className="mb-4">
                  {!collapsed && (
                    <p className="px-3 mb-1 text-xs font-semibold uppercase tracking-widest text-text-tertiary">
                      {group.section}
                    </p>
                  )}
                  {group.items.map((item) => {
                    const b = getBadge(item.href);
                    return (
                      <NavLink
                        key={item.href}
                        item={item}
                        active={isActive(item.href, item.exact)}
                        collapsed={collapsed}
                        badgeLabel={b?.label}
                        badgeVariant={b?.variant}
                      />
                    );
                  })}
                </div>
              ))}
            </>
          ) : (
            <>
              {CLIENT_NAV.map((group) => (
                <div key={group.section} className="mb-4">
                  {!collapsed && (
                    <p className="px-3 mb-1 text-xs font-semibold uppercase tracking-widest text-text-tertiary">
                      {group.section}
                    </p>
                  )}
                  {group.items.map((item) => {
                    const b = getBadge(item.href);
                    return (
                      <NavLink
                        key={item.href}
                        item={item}
                        active={isActive(item.href, item.exact)}
                        collapsed={collapsed}
                        badgeLabel={b?.label}
                        badgeVariant={b?.variant}
                      />
                    );
                  })}
                </div>
              ))}

              {isAdmin && (
                <div className="mt-2 pt-4 border-t border-border-subtle">
                  {!collapsed && (
                    <p className="px-3 mb-1 text-xs font-semibold uppercase tracking-widest text-text-tertiary">
                      Admin
                    </p>
                  )}
                  {ADMIN_NAV_FLAT.slice(0, 2).map((item) => (
                    <NavLink
                      key={item.href}
                      item={item}
                      active={isActive(item.href, item.exact)}
                      collapsed={collapsed}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </nav>

        {!collapsed && !isBackoffice && me?.customer && (
          <PlanWidget customerStatus={me.customer.status} subscription={activeSub} />
        )}
      </aside>
    </>
  );
}
