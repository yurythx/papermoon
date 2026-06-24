"use client";

import { useState, useEffect, useRef, useId } from "react";
import Link from "next/link";
import {
  Menu, X, ChevronDown, Shield, MessageSquare, Filter,
  Wrench, Eye, Server, HardDrive, Cloud, LayoutDashboard,
  MessageCircle, Monitor, Users, FolderOpen,
  Network, Layers, Cpu, Archive, Globe, KeyRound, Building2, FileText, ShieldCheck,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { ThemeToggle } from "@/components/ui/theme-toggle";

type ServiceEntry = {
  label: string;
  href: string;
  icon: React.ElementType;
  color: string;
};

const NAV_TONES = {
  whatsapp: "text-service-whatsapp",
  accent: "text-brand-accent",
  info: "text-info",
  warning: "text-warning",
  success: "text-success",
  neutral: "text-text-secondary",
} as const;

const SERVICES_NAV: ServiceEntry[] = [
  // Comunicação e automação
  { label: "WhatsApp via API Meta",        href: "/servicos/whatsapp-api",       icon: Shield,          color: NAV_TONES.whatsapp },
  { label: "WhatsApp via Evolution API",   href: "/servicos/whatsapp-evolution",  icon: MessageCircle,   color: NAV_TONES.success },
  { label: "Evolution API",               href: "/servicos/evolution-api",       icon: MessageCircle,   color: NAV_TONES.success },
  { label: "Chatwoot",                    href: "/servicos/chatwoot",            icon: MessageSquare,   color: NAV_TONES.info },
  { label: "n8n — Automações",            href: "/servicos/n8n",                 icon: Filter,          color: NAV_TONES.warning },
  // Gestão de TI
  { label: "GLPI Helpdesk",               href: "/servicos/glpi",                icon: Wrench,          color: NAV_TONES.info },
  { label: "Zabbix",                      href: "/servicos/zabbix",              icon: Eye,             color: NAV_TONES.accent },
  // Infraestrutura
  { label: "Proxmox VE",                  href: "/servicos/proxmox",             icon: Server,          color: NAV_TONES.warning },
  { label: "TrueNAS",                     href: "/servicos/truenas",             icon: HardDrive,       color: NAV_TONES.info },
  { label: "Nextcloud",                   href: "/servicos/nextcloud",           icon: Cloud,           color: NAV_TONES.info },
  { label: "AAPanel",                     href: "/servicos/aapanel",             icon: LayoutDashboard, color: NAV_TONES.success },
  // Acesso remoto e servidores
  { label: "RustDesk",                    href: "/servicos/rustdesk",            icon: Monitor,         color: NAV_TONES.warning },
  { label: "Windows Server",              href: "/servicos/windows-server",      icon: Users,           color: NAV_TONES.info },
  { label: "Samba — Arquivos",            href: "/servicos/samba",               icon: FolderOpen,      color: NAV_TONES.neutral },
  // Segurança e identidade
  { label: "Keycloak — SSO",              href: "/servicos/keycloak",            icon: KeyRound,        color: NAV_TONES.accent },
  { label: "Tailscale — Mesh VPN",        href: "/servicos/tailscale",           icon: Network,         color: NAV_TONES.info },
  { label: "CrowdSec",                    href: "/servicos/crowdsec",            icon: ShieldCheck,     color: NAV_TONES.success },
  // Produtividade e CRM
  { label: "Twenty CRM",                  href: "/servicos/twenty-crm",          icon: Building2,       color: NAV_TONES.success },
  { label: "Papermark — Documentos",      href: "/servicos/papermark",           icon: FileText,        color: NAV_TONES.neutral },
  { label: "Plone CMS",                   href: "/servicos/plone",               icon: Globe,           color: NAV_TONES.info },
  // Redes e infraestrutura física
  { label: "Redes Corporativas",          href: "/servicos/redes",               icon: Network,         color: NAV_TONES.info },
  { label: "Cabeamento Estruturado",      href: "/servicos/cabeamento",          icon: Layers,          color: NAV_TONES.neutral },
  { label: "Manutenção Preventiva",       href: "/servicos/manutencao",          icon: Cpu,             color: NAV_TONES.warning },
  { label: "Backup Gerenciado",           href: "/servicos/backup",              icon: Archive,         color: NAV_TONES.success },
];

const LINKS = [
  { label: "Sobre",          href: "/sobre" },
  { label: "Como funciona",  href: "/#como-funciona" },
  { label: "FAQ",            href: "/#faq" },
  { label: "Contato",        href: "/#contato" },
];

export function LandingNav() {
  const [open, setOpen] = useState(false);
  const [servicesOpen, setServicesOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const servicesMenuId = useId();
  const mobileMenuId = useId();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setServicesOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setServicesOpen(false);
        setOpen(false);
      }
    }

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-surface-0/80 backdrop-blur-xl border-b border-border-subtle shadow-md"
          : "bg-transparent"
      )}
    >
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <PaperMoonMark idSuffix="nav" />
          <span className="text-base font-bold text-text-primary tracking-tight">PaperMoon</span>
        </Link>

        <nav aria-label="Navegação principal" className="hidden md:flex items-center gap-7">
          {/* Serviços dropdown — lista plana */}
          <div ref={dropdownRef} className="relative">
            <button
              type="button"
              onClick={() => setServicesOpen((o) => !o)}
              aria-expanded={servicesOpen}
              aria-haspopup="menu"
              aria-controls={servicesMenuId}
              className="flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0"
            >
              Serviços
              <ChevronDown
                size={13}
                className={cn("transition-transform duration-200", servicesOpen && "rotate-180")}
              />
            </button>

            {servicesOpen && (
              <div
                id={servicesMenuId}
                role="menu"
                aria-label="Serviços"
                className="absolute top-full left-1/2 -translate-x-1/2 mt-3 w-[820px] rounded-2xl border border-border-subtle bg-surface-1/95 backdrop-blur-xl shadow-xl p-3 animate-in fade-in slide-in-from-top-1 duration-150"
              >
                <div className="grid grid-cols-4 gap-0.5">
                  {SERVICES_NAV.map((svc) => {
                    const Icon = svc.icon;
                    return (
                      <Link
                        key={svc.href}
                        href={svc.href}
                        onClick={() => setServicesOpen(false)}
                        role="menuitem"
                        className="flex items-center gap-2.5 px-2 py-2 rounded-xl hover:bg-surface-2 transition-colors group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-inset"
                      >
                        <Icon size={13} className={svc.color} />
                        <span className="text-xs text-text-secondary group-hover:text-text-primary transition-colors truncate">
                          {svc.label}
                        </span>
                      </Link>
                    );
                  })}
                </div>
                <div className="mt-2 pt-2 border-t border-border-subtle">
                  <Link
                    href="/servicos"
                    onClick={() => setServicesOpen(false)}
                    role="menuitem"
                    className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-semibold text-brand-accent hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-inset"
                  >
                    Ver todos os serviços
                    <ArrowRight size={11} />
                  </Link>
                </div>
              </div>
            )}
          </div>

          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="rounded-lg text-sm text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3 shrink-0">
          <ThemeToggle />
          <Link
            href="/login"
            className="rounded-lg px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0"
          >
            Entrar
          </Link>
          <Link
            href="/login"
            className="rounded-xl bg-brand-accent px-5 py-2.5 text-sm font-semibold text-[rgb(var(--papermoon-midnight-fixed-rgb))] hover:bg-brand-accent/90 active:scale-95 transition-all shadow-lg shadow-glow-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0"
          >
            Começar agora
          </Link>
        </div>

        <button
          type="button"
          className="md:hidden p-2 rounded-md text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0"
          onClick={() => setOpen((o) => !o)}
          aria-label="Menu"
          aria-expanded={open}
          aria-controls={mobileMenuId}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div
          id={mobileMenuId}
          className="md:hidden bg-surface-1/95 backdrop-blur-xl border-t border-border-subtle px-6 py-5 space-y-1 animate-slide-up"
        >
          <p className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest px-2 pb-2">
            Serviços
          </p>
          {SERVICES_NAV.map((svc) => {
            const Icon = svc.icon;
            return (
              <Link
                key={svc.href}
                href={svc.href}
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 py-2 px-2 text-sm text-text-secondary hover:text-text-primary transition-colors rounded-lg hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-inset"
              >
                <Icon size={14} className={svc.color} />
                {svc.label}
              </Link>
            );
          })}
          <Link
            href="/servicos"
            onClick={() => setOpen(false)}
            className="flex items-center gap-1.5 py-2 px-2 text-sm font-semibold text-brand-accent rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-inset"
          >
            Ver todos os serviços
            <ArrowRight size={13} />
          </Link>

          <div className="pt-3 border-t border-border-subtle space-y-1">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="block rounded-lg py-2.5 text-sm text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-inset"
              >
                {l.label}
              </a>
            ))}
          </div>

          <div className="pt-4 border-t border-border-subtle space-y-3">
            <Link
              href="/login"
              className="block rounded-lg py-2.5 text-center text-sm font-medium text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-inset"
            >
              Entrar
            </Link>
            <Link
              href="/login"
              className="block rounded-xl bg-brand-accent py-3 text-center text-sm font-semibold text-[rgb(var(--papermoon-midnight-fixed-rgb))] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-inset"
            >
              Começar agora
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
