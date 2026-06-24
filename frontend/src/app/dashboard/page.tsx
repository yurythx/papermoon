"use client";

import { memo } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { customerService, licenseService, invoiceService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/compound/status-badge";
import { TimeProgress } from "@/components/compound/time-progress";
import { Button } from "@/components/ui/button";
import {
  Key,
  CreditCard,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Clock,
  ShoppingBag,
  ExternalLink,
  HeadphonesIcon,
  Zap,
  MessageSquare,
  Package,
  Layers,
  MonitorDot,
  Ticket,
  Server,
  HardDrive,
  Cloud,
  LayoutDashboard,
  Network,
  Mail,
  Monitor,
  FolderOpen,
  Globe,
  KeyRound,
  Building2,
  FileText,
  ShieldCheck,
  Archive,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ServiceAccess } from "@/types";

/* -- Service icon mapping --------------------------------------------- */

const SERVICE_TONES = {
  accent: {
    bgColor: "bg-brand-accent/10 border-brand-accent/20",
    iconBg: "bg-brand-accent/10 border-brand-accent/30",
    iconColor: "text-brand-accent",
  },
  whatsapp: {
    bgColor: "bg-service-whatsapp/10 border-service-whatsapp/20",
    iconBg: "bg-service-whatsapp/10 border-service-whatsapp/30",
    iconColor: "text-service-whatsapp",
  },
  success: {
    bgColor: "bg-success-muted border-success/20",
    iconBg: "bg-success-muted border-success/25",
    iconColor: "text-success",
  },
  info: {
    bgColor: "bg-info-muted border-info/20",
    iconBg: "bg-info-muted border-info/25",
    iconColor: "text-info",
  },
  warning: {
    bgColor: "bg-warning-muted border-warning/20",
    iconBg: "bg-warning-muted border-warning/25",
    iconColor: "text-warning",
  },
  neutral: {
    bgColor: "bg-surface-2 border-border-subtle",
    iconBg: "bg-surface-2 border-border-default",
    iconColor: "text-text-tertiary",
  },
} as const;

const SERVICE_MAP: Record<string, { label: string; desc: string; bgColor: string; iconBg: string; iconColor: string; icon: React.ElementType }> = {
  chatwoot:        { label: "Chatwoot",           desc: "Inbox multiagente",      ...SERVICE_TONES.info,      icon: HeadphonesIcon },
  whatsapp_api:    { label: "WhatsApp API",       desc: "API oficial Meta",       ...SERVICE_TONES.whatsapp,  icon: MessageSquare },
  waba:            { label: "WhatsApp Business",  desc: "API oficial Meta",       ...SERVICE_TONES.whatsapp,  icon: MessageSquare },
  meta_whatsapp:   { label: "WhatsApp Meta",      desc: "API oficial Meta",       ...SERVICE_TONES.whatsapp,  icon: MessageSquare },
  evolution_api:   { label: "Evolution API",      desc: "WhatsApp não-oficial",   ...SERVICE_TONES.success,   icon: MessageSquare },
  n8n:             { label: "n8n",                desc: "Automação visual",       ...SERVICE_TONES.warning,   icon: Zap },
  glpi:            { label: "GLPI Helpdesk",      desc: "Gestão de chamados",     ...SERVICE_TONES.info,      icon: Ticket },
  zabbix:          { label: "Zabbix",             desc: "Monitoramento ITIL",     ...SERVICE_TONES.accent,    icon: MonitorDot },
  proxmox:         { label: "Proxmox VE",         desc: "Virtualização",          ...SERVICE_TONES.warning,   icon: Server },
  truenas:         { label: "TrueNAS",            desc: "Storage / NAS",          ...SERVICE_TONES.info,      icon: HardDrive },
  nextcloud:       { label: "Nextcloud",          desc: "Nuvem privada",          ...SERVICE_TONES.info,      icon: Cloud },
  aapanel:         { label: "AAPanel",            desc: "Hospedagem web",         ...SERVICE_TONES.accent,    icon: LayoutDashboard },
  rustdesk:        { label: "RustDesk",           desc: "Acesso remoto seguro",   ...SERVICE_TONES.success,   icon: Monitor },
  samba:           { label: "Samba",              desc: "Servidor de arquivos",   ...SERVICE_TONES.neutral,   icon: FolderOpen },
  "windows-server": { label: "Windows Server",   desc: "Active Directory / AD",  ...SERVICE_TONES.info,      icon: Server },
  plone:           { label: "Plone CMS",          desc: "Portal / intranet",      ...SERVICE_TONES.neutral,   icon: Globe },
  keycloak:        { label: "Keycloak",           desc: "SSO / IAM",              ...SERVICE_TONES.warning,   icon: KeyRound },
  tailscale:       { label: "Tailscale",          desc: "Rede mesh privada",      ...SERVICE_TONES.info,      icon: Network },
  twenty_crm:      { label: "Twenty CRM",         desc: "CRM open-source",        ...SERVICE_TONES.accent,    icon: Building2 },
  papermark:       { label: "Papermark",          desc: "Documentos rastreados",  ...SERVICE_TONES.neutral,   icon: FileText },
  crowdsec:        { label: "CrowdSec",           desc: "Proteção colaborativa",  ...SERVICE_TONES.success,   icon: ShieldCheck },
  backup:          { label: "Backup Corporativo", desc: "Política 3-2-1",         ...SERVICE_TONES.neutral,   icon: Archive },
  network:         { label: "Rede corporativa",   desc: "Infraestrutura física",  ...SERVICE_TONES.neutral,   icon: Network },
};

function getServiceInfo(key: string) {
  return SERVICE_MAP[key.toLowerCase()] ?? {
    label: key,
    desc: "Serviço provisionado",
    bgColor: "bg-brand-accent/10 border-brand-accent/20",
    iconBg: "bg-brand-accent/10 border-brand-accent/30",
    iconColor: "text-brand-accent",
    icon: Package,
  };
}

const SERVICE_STATUS_LABELS: Record<string, string> = {
  active: "Ativo",
  provisioning: "Provisionando...",
  suspended: "Suspenso",
  failed: "Falhou",
};

/* -- ServiceCard ------------------------------------------------------ */

interface ServiceCardProps {
  service: ServiceAccess;
  productName: string;
}

const ServiceCard = memo(function ServiceCard({ service, productName }: ServiceCardProps) {
  const info = getServiceInfo(service.service_key);
  const Icon = info.icon;
  const isActive = service.status === "active";
  const isProvisioning = service.status === "provisioning";

  return (
    <div className={cn(
      "relative rounded-xl border p-5 flex flex-col gap-4 transition-all duration-200 hover:border-border-focus group",
      info.bgColor,
      "bg-surface-1"
    )}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border", info.iconBg)}>
          <Icon size={18} className={info.iconColor} />
        </div>
        <div className={cn(
          "flex items-center gap-1.5 text-[10px] font-semibold px-2 py-1 rounded-full border",
          isActive ? "bg-success-muted border-success/25 text-success" :
          isProvisioning ? "bg-info-muted border-info/25 text-info" :
          "bg-danger-muted border-danger/25 text-danger"
        )}>
          <span className={cn(
            "w-1.5 h-1.5 rounded-full",
            isActive ? "bg-success animate-pulse" :
            isProvisioning ? "bg-info animate-pulse" :
            "bg-danger"
          )} />
          {SERVICE_STATUS_LABELS[service.status] ?? service.status}
        </div>
      </div>

      {/* Info */}
      <div className="flex-1">
        <p className="text-sm font-semibold text-text-primary">{info.label}</p>
        <p className="text-xs text-text-tertiary mt-0.5">{info.desc}</p>
        <p className="text-[11px] text-text-tertiary mt-1 truncate opacity-60">{productName}</p>
      </div>

      {/* CTA */}
      {isActive && (service.service_url ?? (service.external_id?.startsWith("http") ? service.external_id : null)) && (
        <a
          href={service.service_url ?? service.external_id!}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-text-tertiary hover:text-text-primary transition-colors group-hover:text-text-secondary"
        >
          <ExternalLink size={11} />
          Acessar
        </a>
      )}
    </div>
  );
});

/* -- StatusCard ------------------------------------------------------- */

type CardStatus = "success" | "warning" | "danger" | "neutral";

const CARD_STATUS_CLASSES: Record<CardStatus, string> = {
  success: "border-success/20 bg-success-muted",
  warning: "border-warning/20 bg-warning-muted",
  danger: "border-danger/20 bg-danger-muted",
  neutral: "border-border-subtle bg-surface-1",
};

const ICON_STATUS_CLASSES: Record<CardStatus, string> = {
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  neutral: "text-text-tertiary",
};

const VALUE_STATUS_CLASSES: Record<CardStatus, string> = {
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  neutral: "text-text-primary",
};

interface StatusCardProps {
  label: string;
  value: string | number | null;
  icon: React.ElementType;
  href: string;
  status: CardStatus;
}

const StatusCard = memo(function StatusCard({ label, value, icon: Icon, href, status }: StatusCardProps) {
  return (
    <Link href={href} className="block group">
      <div className={cn(
        "rounded-xl p-5 border transition-all duration-150 group-hover:border-border-focus",
        CARD_STATUS_CLASSES[status]
      )}>
        <div className="flex items-start justify-between mb-3">
          <p className="text-xs text-text-secondary font-medium">{label}</p>
          <Icon size={15} className={ICON_STATUS_CLASSES[status]} />
        </div>
        {value === null ? (
          <Skeleton className="h-7 w-24" />
        ) : (
          <p className={cn("text-2xl font-bold tabular-nums", VALUE_STATUS_CLASSES[status])}>
            {value}
          </p>
        )}
      </div>
    </Link>
  );
});

/* -- AlertCard -------------------------------------------------------- */

const ALERT_COLORS = {
  warning: { border: "border-warning/20", bg: "bg-warning-muted", icon: "text-warning", title: "text-warning" },
  danger:  { border: "border-danger/20",  bg: "bg-danger-muted",  icon: "text-danger",  title: "text-danger"  },
} as const;

interface AlertCardProps {
  variant: "warning" | "danger";
  title: string;
  description: string;
  ctaLabel: string;
  ctaHref: string;
}

const AlertCard = memo(function AlertCard({ variant, title, description, ctaLabel, ctaHref }: AlertCardProps) {
  const c = ALERT_COLORS[variant];
  return (
    <div className={cn("rounded-xl border p-4 flex items-start gap-3", c.border, c.bg)}>
      <AlertTriangle size={15} className={cn(c.icon, "shrink-0 mt-0.5")} />
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm font-semibold", c.title)}>{title}</p>
        <p className="text-xs text-text-secondary mt-0.5 truncate">{description}</p>
      </div>
      <Link href={ctaHref} className="shrink-0">
        <Button variant={variant === "danger" ? "danger" : "warning"} size="xs">
          {ctaLabel}
        </Button>
      </Link>
    </div>
  );
});

/* -- Page ------------------------------------------------------------- */

export default function DashboardPage() {
  const { me } = useAuth();

  const { data: metrics, isLoading: loadingMetrics } = useQuery({
    queryKey: ["metrics"],
    queryFn: customerService.getMetrics,
    enabled: !!me?.customer,
  });

  const { data: licenses, isLoading: loadingLicenses } = useQuery({
    queryKey: ["licenses"],
    queryFn: licenseService.list,
    enabled: !!me?.customer,
  });

  const { data: overdueInvoices } = useQuery({
    queryKey: ["invoices-overdue"],
    queryFn: () => invoiceService.list({ status: "overdue" }),
    enabled: !!me?.customer,
  });

  const allLicenses = licenses?.results ?? [];
  const activeLicenses = allLicenses.filter((l) => l.status === "active");
  const expiringLicenses = activeLicenses.filter((l) => l.days_remaining <= 15);
  const criticalLicenses = expiringLicenses.filter((l) => l.days_remaining <= 7);
  const suspendedLicenses = allLicenses.filter((l) => l.status === "suspended");
  const expiredLicenses = allLicenses.filter((l) => l.status === "expired");
  const overdueCount = overdueInvoices?.results?.length ?? 0;

  const hasAlerts = criticalLicenses.length > 0 || overdueCount > 0 || suspendedLicenses.length > 0 || expiredLicenses.length > 0;

  // Collect all provisioned services across active licenses
  const allServices = activeLicenses.flatMap((l) =>
    (l.services ?? []).map((s) => ({ service: s, productName: l.product_name }))
  );

  const companyName = me?.customer?.company_name ?? "";
  const firstName = companyName.split(" ")[0];

  return (
    <div className="space-y-8">

      {/* -- Hero header ----------------------------------------------- */}
      <div className="relative rounded-2xl overflow-hidden border border-border-subtle bg-surface-1 p-6 md:p-8">
        {/* Background glow */}
        <div className="pointer-events-none absolute -top-10 right-0 w-72 h-56 bg-brand-accent/10 blur-3xl rounded-full" />
        <div className="pointer-events-none absolute bottom-0 left-24 w-48 h-40 bg-slate-400/10 blur-3xl rounded-full" />
        {/* Subtle grid */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.025]"
          style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "24px 24px" }}
        />

        <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-5">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl md:text-3xl font-black text-text-primary tracking-tight">
                Olá,{" "}
                <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
                  {firstName || "bem-vindo"}
                </span>
              </h1>
              {me?.customer && <StatusBadge status={me.customer.status} />}
            </div>
            <p className="text-sm text-text-secondary flex items-center gap-2">
              <Layers size={13} className="text-text-tertiary" />
              {companyName || "Sua conta PaperMoon"}
            </p>
          </div>

          <a href="mailto:contato@papermoon.com.br">
            <Button variant="secondary" size="sm">
              <Mail size={14} className="mr-1.5" />
              Falar com a equipe
            </Button>
          </a>
        </div>
      </div>

      {/* -- KPI cards ------------------------------------------------- */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 md:gap-4">
        <StatusCard
          label="Licenças Ativas"
          value={loadingLicenses ? null : activeLicenses.length}
          icon={Key}
          href="/dashboard/licenses"
          status={activeLicenses.length === 0 ? "neutral" : "success"}
        />
        <StatusCard
          label="Total Pago"
          value={loadingMetrics ? null : `R$ ${(metrics?.total_paid ?? 0).toFixed(2)}`}
          icon={TrendingUp}
          href="/dashboard/invoices"
          status="neutral"
        />
        <StatusCard
          label="Pendente"
          value={loadingMetrics ? null : `R$ ${(metrics?.total_pending ?? 0).toFixed(2)}`}
          icon={Clock}
          href="/dashboard/invoices"
          status={metrics && metrics.total_pending > 0 ? "warning" : "neutral"}
        />
        <StatusCard
          label="Vencidas"
          value={loadingMetrics ? null : `R$ ${(metrics?.total_overdue ?? 0).toFixed(2)}`}
          icon={CreditCard}
          href="/dashboard/invoices"
          status={metrics && metrics.total_overdue > 0 ? "danger" : "neutral"}
        />
      </div>

      {/* -- Alerts ---------------------------------------------------- */}
      {hasAlerts && (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-widest">Atenção necessária</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {overdueCount > 0 && (
              <AlertCard
                variant="danger"
                title={`${overdueCount} fatura${overdueCount > 1 ? "s" : ""} vencida${overdueCount > 1 ? "s" : ""}`}
                description={`R$ ${(metrics?.total_overdue ?? 0).toFixed(2)} em aberto`}
                ctaLabel="Regularizar"
                ctaHref="/dashboard/invoices"
              />
            )}
            {criticalLicenses.map((l) => (
              <AlertCard
                key={l.id}
                variant="warning"
                title={`${l.product_name} expira em ${l.days_remaining}d`}
                description="Renove agora para não perder o acesso"
                ctaLabel="Ver licença"
                ctaHref={`/dashboard/licenses/${l.id}`}
              />
            ))}
            {suspendedLicenses.length > 0 && (
              <AlertCard
                variant="warning"
                title={`${suspendedLicenses.length} licença${suspendedLicenses.length > 1 ? "s" : ""} suspensa${suspendedLicenses.length > 1 ? "s" : ""}`}
                description={suspendedLicenses.map((l) => l.product_name).join(", ")}
                ctaLabel="Reativar"
                ctaHref="/dashboard/subscriptions"
              />
            )}
            {expiredLicenses.length > 0 && (
              <AlertCard
                variant="danger"
                title={`${expiredLicenses.length} licença${expiredLicenses.length > 1 ? "s" : ""} expirada${expiredLicenses.length > 1 ? "s" : ""}`}
                description="Renove para restaurar o acesso"
                ctaLabel="Ver catálogo"
                ctaHref="/dashboard/catalog"
              />
            )}
          </div>
        </section>
      )}

      {/* -- Meus Serviços --------------------------------------------- */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-widest">Meus Serviços</h2>
          <Link href="/dashboard/licenses" className="text-xs text-brand-accent hover:underline flex items-center gap-1">
            Ver licenças <ArrowRight size={11} />
          </Link>
        </div>

        {loadingLicenses ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-36 rounded-xl" />)}
          </div>
        ) : allServices.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border-default bg-surface-1 p-8 text-center">
            <div className="w-12 h-12 rounded-xl bg-surface-2 border border-border-subtle flex items-center justify-center mx-auto mb-4">
              <Package size={20} className="text-text-tertiary" />
            </div>
            <p className="text-sm font-medium text-text-primary mb-1">Nenhum serviço ativo</p>
            <p className="text-xs text-text-secondary mb-4">
              Explore o catálogo e contrate o serviço certo para a sua operação.
            </p>
            <Link href="/dashboard/catalog">
              <Button variant="primary" size="sm">
                <ShoppingBag size={13} className="mr-1.5" />
                Explorar catálogo
              </Button>
            </Link>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {allServices.map(({ service, productName }, i) => (
              <ServiceCard key={`${service.id}-${i}`} service={service} productName={productName} />
            ))}
          </div>
        )}
      </section>

      {/* -- Licenças ativas ------------------------------------------- */}
      {activeLicenses.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-widest">Licenças Ativas</h2>
            <Link href="/dashboard/licenses" className="text-xs text-brand-accent hover:underline flex items-center gap-1">
              Ver todas <ArrowRight size={11} />
            </Link>
          </div>

          <div className="space-y-3">
            {activeLicenses.slice(0, 3).map((l) => (
              <Link key={l.id} href={`/dashboard/licenses/${l.id}`} className="block group">
                <div className="bg-surface-1 border border-border-subtle rounded-xl p-5 hover:border-border-focus transition-all duration-150">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-sm font-semibold text-text-primary group-hover:text-white transition-colors">
                        {l.product_name}
                      </p>
                      <p className="text-xs text-text-tertiary font-mono mt-0.5">
                        {l.key.slice(0, 16)}…
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-text-secondary">
                        R$ {parseFloat(l.amount).toFixed(2)}/{l.billing_cycle === "monthly" ? "mês" : "ano"}
                      </span>
                      <StatusBadge status={l.status} />
                    </div>
                  </div>
                  <TimeProgress startDate={l.valid_from ?? l.created_at} endDate={l.valid_until} />
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
