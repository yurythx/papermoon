import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, ArrowLeft, Check } from "lucide-react";
import { LandingNav } from "@/components/marketing/nav";
import { Footer } from "@/components/marketing/footer";
import { Badge } from "@/components/ui/badge";
import { cardClass } from "@/components/ui/card";
import { ArrowLink } from "@/components/compound/arrow-link";
import { SERVICES } from "@/lib/services-content";
import { fetchActiveServiceSlugs, isServiceVisible } from "@/lib/active-services";

const _siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://papermoon.cloud";
const _serviceCount = SERVICES.length;
const _serviceCountText = `${_serviceCount} serviços de TI instalados, configurados e mantidos pela PaperMoon na sua infraestrutura.`;

const _breadcrumbSchema = {
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  itemListElement: [
    { "@type": "ListItem", position: 1, name: "Início", item: _siteUrl },
    { "@type": "ListItem", position: 2, name: "Serviços", item: `${_siteUrl}/servicos` },
  ],
};

const _ogImage =
  `${_siteUrl}/api/og?` +
  new URLSearchParams({
    title: "Todos os Serviços",
    desc: _serviceCountText,
    tag: "Portfólio completo",
  }).toString();

export const metadata: Metadata = {
  title: "Todos os Serviços — PaperMoon",
  description:
    "Conheça todos os serviços de TI gerenciados pela PaperMoon: WhatsApp API, Chatwoot, n8n, GLPI, Zabbix, Proxmox, Tailscale, Keycloak até redes, cabeamento e manutenção.",
  alternates: { canonical: `${_siteUrl}/servicos` },
  openGraph: {
    title: "Todos os Serviços — PaperMoon",
    description: _serviceCountText,
    url: `${_siteUrl}/servicos`,
    siteName: "PaperMoon",
    type: "website",
    images: [{ url: _ogImage, width: 1200, height: 630, alt: "Todos os Serviços — PaperMoon" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Todos os Serviços — PaperMoon",
    description: _serviceCountText,
    images: [_ogImage],
  },
};

const CATEGORIES = [
  { label: "Comunicação",            slugs: ["whatsapp-api", "whatsapp-evolution", "evolution-api", "chatwoot"] },
  { label: "Automação",              slugs: ["n8n"] },
  { label: "Gestão de TI",           slugs: ["glpi", "zabbix"] },
  { label: "Infraestrutura",         slugs: ["proxmox", "truenas", "nextcloud", "aapanel"] },
  { label: "Acesso Remoto",          slugs: ["rustdesk", "windows-server", "samba"] },
  { label: "Segurança e Identidade", slugs: ["keycloak", "tailscale", "crowdsec"] },
  { label: "Produtividade e CRM",    slugs: ["twenty-crm", "papermark", "plone"] },
  { label: "Redes e Física",         slugs: ["redes", "cabeamento", "manutencao", "backup"] },
] as const;

const bySlug = Object.fromEntries(SERVICES.map((s) => [s.slug, s]));

export default async function ServicosPage() {
  const activeSlugs = await fetchActiveServiceSlugs();

  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(_breadcrumbSchema) }} />
      <LandingNav activeSlugs={activeSlugs === null ? null : Array.from(activeSlugs)} />

      {/* Hero */}
      <section className="pt-32 pb-16 border-b border-border-subtle">
        <div className="max-w-5xl mx-auto px-6">
          <Link
            href="/#servicos"
            className="inline-flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors mb-8"
          >
            <ArrowLeft size={12} />
            Voltar para o início
          </Link>

          <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">
            Portfólio completo
          </p>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
            Todos os{" "}
            <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
              serviços
            </span>
          </h1>
          <p className="text-text-secondary max-w-xl text-sm leading-relaxed">
            {_serviceCount} serviços instalados, configurados e mantidos pela PaperMoon na infraestrutura da sua empresa.
            Cada serviço vem com documentação, monitoramento e suporte dedicado.
          </p>

          <div className="mt-8 flex flex-wrap gap-2">
            {[
              "Sem mensalidade SaaS",
              "Instalação na sua VPS",
              "Dados na sua infraestrutura",
              "Suporte especializado",
            ].map((item) => (
              <Badge key={item} variant="muted" pill className="gap-1.5 px-3 py-1.5 text-xs">
                <Check size={10} className="text-brand-accent shrink-0" />
                {item}
              </Badge>
            ))}
          </div>
        </div>
      </section>

      {/* Categorias */}
      <div className="max-w-5xl mx-auto px-6 py-16 space-y-16">
        {CATEGORIES.map((cat) => {
          const services = cat.slugs
            .map((s) => bySlug[s])
            .filter((svc) => svc && isServiceVisible(svc.slug, activeSlugs));
          if (!services.length) return null;

          return (
            <section key={cat.label}>
              <h2 className="text-xs font-bold text-text-tertiary uppercase tracking-widest mb-5">
                {cat.label}
              </h2>

              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {services.map((svc) => {
                  const Icon = svc.icon;
                  return (
                    <Link
                      key={svc.slug}
                      href={`/servicos/${svc.slug}`}
                      className={cardClass({ interactive: true, className: "group relative flex flex-col gap-4" })}
                    >
                      {svc.comingSoon && (
                        <Badge variant="muted" pill className="absolute top-4 right-4 text-[10px] px-2 py-0.5">
                          Em breve
                        </Badge>
                      )}

                      <div className={`w-10 h-10 rounded-xl ${svc.colorBg} border ${svc.colorBorder} flex items-center justify-center`}>
                        <Icon size={18} className={svc.colorText} />
                      </div>

                      <div className="flex-1">
                        <h3 className="text-sm font-bold text-text-primary mb-1">{svc.name}</h3>
                        <p className="text-xs text-text-secondary leading-relaxed line-clamp-3">
                          {svc.tagline}
                        </p>
                      </div>

                      <ArrowLink className={svc.colorText}>Saiba mais</ArrowLink>
                    </Link>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>

      {/* CTA */}
      <section className="border-t border-border-subtle bg-surface-1/30 py-20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">
            Pronto para começar?
          </p>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">
            Quer contratar um serviço?
          </h2>
          <p className="text-text-secondary text-sm mb-8 max-w-md mx-auto">
            Fale com nossa equipe e descubra qual combinação de serviços faz sentido para o momento da sua empresa.
          </p>
          <a
            href="https://wa.me/5511999999999?text=Olá!%20Vim%20do%20site%20da%20PaperMoon%20e%20gostaria%20de%20saber%20mais%20sobre%20os%20serviços."
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-brand-accent text-slate-950 text-sm font-semibold hover:bg-brand-accent/90 active:scale-95 transition-all shadow-lg shadow-glow-accent"
          >
            Falar com a equipe
            <ArrowRight size={14} />
          </a>
        </div>
      </section>

      <Footer idSuffix="servicos" />
    </div>
  );
}
