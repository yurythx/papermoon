import type { Metadata } from "next";
import Link from "next/link";
import {
  Shield,
  MessageCircle,
  MessageSquare,
  Filter,
  Wrench,
  Eye,
  Server,
  HardDrive,
  Cloud,
  LayoutDashboard,
  Monitor,
  ArrowRight,
  Check,
  Users,
  Settings,
  Mail,
  Phone,
  Zap,
  Network,
  Layers,
  Cpu,
  Archive,
  FolderOpen,
  Globe,
  KeyRound,
  Building2,
  FileText,
  ShieldCheck,
} from "lucide-react";
import { LandingNav } from "@/components/marketing/nav";
import { LandingFAQ } from "@/components/marketing/faq";
import { LogosMarquee } from "@/components/marketing/logos-marquee";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { ContactForm } from "@/components/marketing/contact-form";
import { LANDING_FAQS } from "@/lib/faq-content";

const _siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://app.papermoon.com.br";
const _ogHome =
  `${_siteUrl}/api/og?` +
  new URLSearchParams({
    title: "Infraestrutura open-source gerenciada",
    desc: "GLPI, Zabbix, Proxmox, Chatwoot, n8n, Nextcloud, Keycloak e muito mais — na sua VPS, sem vendor lock-in.",
    tag: "PaperMoon",
  }).toString();

export const metadata: Metadata = {
  title: "PaperMoon — Infraestrutura open-source gerenciada para empresas",
  description:
    "A PaperMoon instala e gerencia mais de 20 ferramentas open-source na sua VPS: GLPI, Zabbix, Proxmox, Chatwoot, n8n, Nextcloud, Keycloak, Twenty CRM, CrowdSec e muito mais. Sua infra, seu controle.",
  alternates: { canonical: _siteUrl },
  openGraph: {
    title: "PaperMoon — Infraestrutura open-source gerenciada para empresas",
    description:
      "Mais de 20 ferramentas open-source instaladas e gerenciadas na sua VPS. Sua infra, seu controle.",
    url: _siteUrl,
    siteName: "PaperMoon",
    type: "website",
    images: [{ url: _ogHome, width: 1200, height: 630, alt: "PaperMoon — Infraestrutura gerenciada" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "PaperMoon — Infraestrutura open-source gerenciada para empresas",
    description:
      "Mais de 20 ferramentas open-source instaladas e gerenciadas na sua VPS.",
    images: [_ogHome],
  },
};

/* ------------------------------------------------------------------ */

const DIFFERENTIALS = [
  {
    icon: Server,
    title: "Sua infraestrutura, seu controle",
    description:
      "Tudo instalado na VPS da sua empresa. Você tem acesso root, os dados ficam no seu servidor e nenhum serviço fica preso no nosso ambiente.",
  },
  {
    icon: Settings,
    title: "Stack 100% open-source",
    description:
      "GLPI, Zabbix, Proxmox, Chatwoot, n8n — sem licenças caras ou vendor lock-in. As ferramentas ficam rodando mesmo que você encerre o contrato.",
  },
  {
    icon: Users,
    title: "Equipe treinada e suporte incluso",
    description:
      "Cada implantação inclui treinamento da equipe. Serviços mensais incluem suporte contínuo — não entregamos e desaparecemos.",
  },
];

const LANDING_TONES = {
  whatsapp: { iconColor: "text-service-whatsapp", iconBg: "bg-service-whatsapp/10" },
  accent: { iconColor: "text-brand-accent", iconBg: "bg-brand-accent/10" },
  info: { iconColor: "text-info", iconBg: "bg-info-muted" },
  warning: { iconColor: "text-warning", iconBg: "bg-warning-muted" },
  success: { iconColor: "text-success", iconBg: "bg-success-muted" },
  neutral: { iconColor: "text-text-secondary", iconBg: "bg-surface-2" },
  monthly: "text-brand-accent bg-brand-accent/10 border-brand-accent/20",
  oneTime: "text-warning bg-warning-muted border-warning/20",
} as const;

const SERVICES_LANDING = [
  {
    icon: Shield,
    ...LANDING_TONES.whatsapp,
    name: "WhatsApp via API Meta",
    description:
      "API oficial da Meta + Chatwoot multiagente + n8n automação — instalados na sua VPS. Número verificado, zero risco de ban.",
    billing: "Mensal",
    billingColor: LANDING_TONES.monthly,
    tags: ["WhatsApp API Meta", "Chatwoot", "n8n"],
    href: "/servicos/whatsapp-api",
  },
  {
    icon: MessageCircle,
    ...LANDING_TONES.success,
    name: "WhatsApp via Evolution API",
    description:
      "Evolution API self-hosted + Chatwoot + n8n — múltiplas instâncias WhatsApp na sua VPS, sem custo por mensagem.",
    billing: "Mensal",
    billingColor: LANDING_TONES.monthly,
    tags: ["Evolution API", "Chatwoot", "n8n"],
    href: "/servicos/whatsapp-evolution",
  },
  {
    icon: Wrench,
    ...LANDING_TONES.info,
    name: "GLPI Helpdesk",
    description:
      "Helpdesk ITIL com categorias, SLAs, filas de atendimento, base de conhecimento e treinamento da equipe de TI.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["GLPI"],
    href: "/servicos/glpi",
  },
  {
    icon: Eye,
    ...LANDING_TONES.accent,
    name: "Zabbix",
    description:
      "Monitoramento de servidores e serviços com dashboards em tempo real, triggers configuráveis e alertas automáticos.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Zabbix"],
    href: "/servicos/zabbix",
  },
  {
    icon: Server,
    ...LANDING_TONES.warning,
    name: "Proxmox VE",
    description:
      "Virtualização enterprise open-source: VMs KVM, containers LXC, ZFS e cluster HA no seu servidor dedicado.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Proxmox VE"],
    href: "/servicos/proxmox",
  },
  {
    icon: HardDrive,
    ...LANDING_TONES.info,
    name: "TrueNAS",
    description:
      "Storage centralizado open-source com ZFS, replicação, snapshots agendados e compartilhamento NFS/SMB.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["TrueNAS"],
    href: "/servicos/truenas",
  },
  {
    icon: Cloud,
    ...LANDING_TONES.info,
    name: "Nextcloud",
    description:
      "Nuvem privada na sua VPS: arquivos, calendário, contatos, vídeo e edição de documentos online.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Nextcloud"],
    href: "/servicos/nextcloud",
  },
  {
    icon: LayoutDashboard,
    ...LANDING_TONES.success,
    name: "AAPanel",
    description:
      "Painel web para hospedar sites: Nginx, PHP multi-versão, MySQL, SSL automático e backup agendado.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["AAPanel"],
    href: "/servicos/aapanel",
  },
  {
    icon: Monitor,
    ...LANDING_TONES.warning,
    name: "RustDesk",
    description:
      "Acesso remoto self-hosted open-source: alternativa ao TeamViewer sem custo por dispositivo, criptografia ponta a ponta na sua VPS.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["RustDesk"],
    href: "/servicos/rustdesk",
  },
  {
    icon: Users,
    ...LANDING_TONES.info,
    name: "Windows Server",
    description:
      "Active Directory, servidor de arquivos NTFS, GPOs e integração com Microsoft 365 — infraestrutura Microsoft configurada e gerenciada pela PaperMoon.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Windows Server", "Active Directory"],
    href: "/servicos/windows-server",
  },
  {
    icon: FolderOpen,
    ...LANDING_TONES.neutral,
    name: "Samba — Servidor de Arquivos",
    description:
      "Servidor de arquivos Linux com compartilhamento SMB/CIFS nativo para Windows, macOS e Linux — open-source, sem custo de licença de SO.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Samba", "SMB/CIFS"],
    href: "/servicos/samba",
  },
  {
    icon: Globe,
    ...LANDING_TONES.info,
    name: "Plone CMS",
    description:
      "Portal corporativo e intranet com gestão documental, workflow de publicação e controle de acesso granular — 100% self-hosted.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Plone", "CMS", "Intranet"],
    href: "/servicos/plone",
  },
  {
    icon: KeyRound,
    ...LANDING_TONES.accent,
    name: "Keycloak — IAM e SSO",
    description:
      "Login único para todos os sistemas da empresa: OAuth2, OIDC, SAML 2.0, MFA e integração com Active Directory — sem dependência de nuvem.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Keycloak", "SSO", "OAuth2", "IAM"],
    href: "/servicos/keycloak",
  },
  {
    icon: Network,
    ...LANDING_TONES.info,
    name: "Tailscale",
    description:
      "Rede privada mesh com WireGuard para conectar notebooks, servidores e filiais sem abrir portas no firewall e sem a complexidade de VPN tradicional.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Tailscale", "WireGuard", "Acesso remoto"],
    href: "/servicos/tailscale",
  },
  {
    icon: Building2,
    ...LANDING_TONES.success,
    name: "Twenty CRM",
    description:
      "CRM open-source self-hosted com pipeline de vendas, contatos, empresas e integração de e-mail — alternativa ao Salesforce sem custo por usuário.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Twenty CRM", "CRM", "Vendas"],
    href: "/servicos/twenty-crm",
  },
  {
    icon: FileText,
    ...LANDING_TONES.neutral,
    name: "Papermark",
    description:
      "Compartilhe propostas com link rastreável: saiba quem abriu, tempo por página e nível de interesse — alternativa ao DocSend com dados no seu servidor.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Papermark", "DocSend", "Propostas"],
    href: "/servicos/papermark",
  },
  {
    icon: ShieldCheck,
    ...LANDING_TONES.success,
    name: "CrowdSec",
    description:
      "Proteção automática contra ataques com inteligência de ameaças colaborativa — detecção comportamental e bloqueio de IPs em tempo real na sua infra.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["CrowdSec", "Segurança", "IDS/IPS"],
    href: "/servicos/crowdsec",
  },
  {
    icon: MessageSquare,
    ...LANDING_TONES.info,
    name: "Chatwoot",
    description:
      "Central de atendimento omnichannel open-source. Múltiplos agentes no mesmo número, histórico por contato, etiquetas e SLA — instalado e configurado na sua VPS.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Chatwoot", "Omnichannel", "SLA"],
    href: "/servicos/chatwoot",
  },
  {
    icon: Filter,
    ...LANDING_TONES.warning,
    name: "n8n — Automação",
    description:
      "Automação com mais de 400 integrações nativas. Fluxos de qualificação, bot de FAQ e roteamento — entregues prontos e integrados ao Chatwoot e WhatsApp.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["n8n", "Automação", "Workflows"],
    href: "/servicos/n8n",
  },
  {
    icon: MessageCircle,
    ...LANDING_TONES.accent,
    name: "Evolution API",
    description:
      "Gateway WhatsApp self-hosted com múltiplas instâncias, webhooks granulares e integração nativa com n8n e Chatwoot — sem custo por mensagem enviada.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Evolution API", "WhatsApp", "Webhooks"],
    href: "/servicos/evolution-api",
  },
  {
    icon: Network,
    ...LANDING_TONES.info,
    name: "Redes corporativas",
    description:
      "Projeto e implantação de rede corporativa: switching, VLANs, firewall pfSense, Wi-Fi WPA3 empresarial e VPN — com documentação certificada inclusa.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Redes", "VLANs", "pfSense"],
    href: "/servicos/redes",
  },
  {
    icon: Layers,
    ...LANDING_TONES.neutral,
    name: "Cabeamento estruturado",
    description:
      "Instalação certificada Cat5e, Cat6 e Cat6A com laudo técnico por ponto, fibra óptica, organização de rack e conformidade ABNT NBR 14565.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Cat6", "Fibra", "ABNT NBR 14565"],
    href: "/servicos/cabeamento",
  },
  {
    icon: Cpu,
    ...LANDING_TONES.warning,
    name: "Manutenção de servidores",
    description:
      "Diagnóstico, limpeza, upgrade de componentes e atualização de firmware em servidores Dell, HP e Supermicro — com relatório técnico incluído.",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["Dell", "HP", "Preventiva"],
    href: "/servicos/manutencao",
  },
  {
    icon: Archive,
    ...LANDING_TONES.success,
    name: "Backup corporativo",
    description:
      "Política de backup 3-2-1 com RPO/RTO definidos, criptografia AES-256, testes de restore documentados e Plano de Recuperação de Desastres (DRP).",
    billing: "Cobrança Única",
    billingColor: LANDING_TONES.oneTime,
    tags: ["DRP", "3-2-1", "BorgBackup"],
    href: "/servicos/backup",
  },
];

const HOW_IT_WORKS = [
  {
    num: "01",
    icon: Server,
    title: "Você contrata uma VPS",
    description:
      "Escolha qualquer provedor (Hostinger, Hetzner, AWS...) com as especificações que a PaperMoon indicar. O servidor é seu — você paga direto ao provedor, sem intermediários.",
  },
  {
    num: "02",
    icon: Settings,
    title: "Instalamos e configuramos",
    description:
      "A PaperMoon acessa o servidor via SSH e faz toda a instalação, configuração e integração entre os serviços. Segurança, SSL, backup e monitoramento inclusos.",
  },
  {
    num: "03",
    icon: Users,
    title: "Treinamos sua equipe",
    description:
      "Após a entrega, treinamos quem vai operar os serviços. Suporte contínuo via WhatsApp e e-mail para manter tudo funcionando.",
  },
];

const FIELD_EXPERTISE = [
  {
    icon: Network,
    color: "text-info",
    bg: "bg-info-muted border-info/20",
    href: "/servicos/redes",
    title: "Redes e conectividade",
    items: [
      "Design e planejamento de redes LAN, WAN e Wi-Fi",
      "Configuração de switches, roteadores e firewalls",
      "Segmentação de rede com VLANs",
      "VPN corporativa e acesso remoto seguro",
      "Diagnóstico e otimização de redes existentes",
    ],
  },
  {
    icon: Layers,
    color: "text-text-secondary",
    bg: "bg-surface-2 border-border-subtle",
    href: "/servicos/cabeamento",
    title: "Cabeamento estruturado",
    items: [
      "Projeto e instalação Cat5e, Cat6 e Cat6A",
      "Cabeamento óptico (fibra monomodo e multimodo)",
      "Organização de racks e patch panels",
      "Certificação de links com equipamentos profissionais",
      "Conformidade com ABNT NBR 14565",
    ],
  },
  {
    icon: Cpu,
    color: "text-warning",
    bg: "bg-warning-muted border-warning/20",
    href: "/servicos/manutencao",
    title: "Servidores e computadores",
    items: [
      "Manutenção preventiva e corretiva",
      "Upgrade de hardware (RAM, SSD, processadores)",
      "Montagem de servidores sob medida",
      "Instalação e configuração de Windows Server e Linux",
      "Diagnóstico e substituição de componentes",
    ],
  },
  {
    icon: Archive,
    color: "text-success",
    bg: "bg-success-muted border-success/20",
    href: "/servicos/backup",
    title: "Backup completo para servidores",
    items: [
      "Diagnóstico e projeto de política de backup",
      "Backup local, em rede (NAS) e em nuvem",
      "Agendamento automático com retenção configurável",
      "Testes regulares de restauração (DRP)",
      "Integração com TrueNAS, Proxmox Backup Server e cloud",
    ],
  },
];

const TOOL_BADGES = [
  "WhatsApp API Meta",
  "Evolution API",
  "Chatwoot",
  "n8n",
  "GLPI",
  "Zabbix",
  "Proxmox VE",
  "TrueNAS",
  "Nextcloud",
  "AAPanel",
  "RustDesk",
  "Windows Server",
  "Samba",
];

/* ------------------------------------------------------------------ */

const _orgSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "PaperMoon",
  url: "https://app.papermoon.com.br",
  contactPoint: {
    "@type": "ContactPoint",
    contactType: "customer support",
    email: "contato@papermoon.com.br",
    availableLanguage: "Portuguese",
  },
  sameAs: [],
};

const _faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: LANDING_FAQS.map((item) => ({
    "@type": "Question",
    name: item.q,
    acceptedAnswer: { "@type": "Answer", text: item.a },
  })),
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(_orgSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(_faqSchema) }} />
      <LandingNav />

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative min-h-[90vh] flex flex-col justify-center pt-16 overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-to-b from-brand-accent/20 via-brand-accent/10 to-transparent blur-3xl rounded-full" />
          <div className="absolute top-60 -left-32 w-96 h-96 bg-brand-accent/10 blur-3xl rounded-full" />
          <div className="absolute top-40 -right-32 w-96 h-96 bg-slate-500/10 blur-3xl rounded-full" />
          <div
            className="absolute inset-0 opacity-[0.02]"
            style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "32px 32px" }}
          />
        </div>

        <div className="max-w-5xl mx-auto px-6 py-24 lg:py-32 w-full text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-brand-accent/30 bg-brand-accent/10 text-brand-accent text-xs font-semibold mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-accent animate-pulse" />
            Infraestrutura open-source gerenciada para empresas
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-[1.05] mb-6">
            Servidores e ferramentas{" "}
            <span className="bg-gradient-to-r from-brand-accent via-warning/70 to-text-primary bg-clip-text text-transparent">
              open-source
            </span>
            <br className="hidden sm:block" />
            {" "}gerenciados para a sua empresa
          </h1>

          <p className="text-base sm:text-lg text-text-secondary leading-relaxed max-w-2xl mx-auto mb-8">
            A PaperMoon instala, configura e mantém as melhores ferramentas open-source na VPS da sua empresa —
            da comunicação ao monitoramento, do helpdesk à virtualização.
            Você tem controle total. Nós garantimos que funciona.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-12">
            <a
              href="#servicos"
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-brand-accent text-slate-950 font-semibold text-sm hover:bg-brand-accent/90 active:scale-95 transition-all shadow-xl shadow-glow-accent"
            >
              Ver serviços
              <ArrowRight size={16} />
            </a>
            <a
              href="#contato"
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-surface-2 border border-border-default text-text-primary font-semibold text-sm hover:bg-surface-3 hover:border-border-focus transition-all"
            >
              Falar com a equipe
            </a>
          </div>

          <div className="flex flex-wrap justify-center gap-2">
            {TOOL_BADGES.map((tool) => (
              <span
                key={tool}
                className="px-3 py-1.5 rounded-lg bg-surface-1 border border-border-subtle text-xs font-medium text-text-secondary"
              >
                {tool}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Diferenciais ─────────────────────────────────────────────── */}
      <section className="py-20 sm:py-24 border-t border-border-subtle">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid sm:grid-cols-3 gap-6">
            {DIFFERENTIALS.map((d, i) => {
              const Icon = d.icon;
              return (
                <div key={i} className="p-6 rounded-2xl bg-surface-1 border border-border-subtle space-y-3">
                  <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                    <Icon size={18} className="text-brand-accent" />
                  </div>
                  <h3 className="text-sm font-bold text-text-primary">{d.title}</h3>
                  <p className="text-xs text-text-secondary leading-relaxed">{d.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Serviços ─────────────────────────────────────────────────── */}
      <section id="servicos" className="py-24 sm:py-32 border-t border-border-subtle bg-surface-1/30">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">Portfólio completo</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Nossos{" "}
              <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
                serviços
              </span>
            </h2>
            <p className="text-text-secondary mt-3 max-w-xl mx-auto text-sm">
              Todos instalados, configurados e mantidos pela PaperMoon na infraestrutura da sua empresa.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5" id="servicos-grid">
            {SERVICES_LANDING.map((svc, i) => {
              const Icon = svc.icon;
              return (
                <Link
                  key={i}
                  href={svc.href}
                  className="group rounded-2xl bg-surface-1 border border-border-subtle p-5 flex flex-col gap-4 hover:border-border-focus transition-all duration-150"
                >
                  <div className="flex items-start justify-between">
                    <div className={`w-10 h-10 rounded-xl ${svc.iconBg} flex items-center justify-center`}>
                      <Icon size={18} className={svc.iconColor} />
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${svc.billingColor}`}>
                      {svc.billing}
                    </span>
                  </div>

                  <div className="flex-1">
                    <h3 className="text-sm font-bold text-text-primary mb-1.5">{svc.name}</h3>
                    <p className="text-xs text-text-secondary leading-relaxed">{svc.description}</p>
                  </div>

                  <div className="flex flex-wrap gap-1.5">
                    {svc.tags.map((tag) => (
                      <span key={tag} className="text-[10px] px-2 py-0.5 rounded-md bg-surface-2 border border-border-subtle text-text-tertiary font-medium">
                        {tag}
                      </span>
                    ))}
                  </div>

                  <span className={`inline-flex items-center gap-1 text-xs font-semibold ${svc.iconColor} group-hover:underline`}>
                    Saiba mais
                    <ArrowRight size={11} />
                  </span>
                </Link>
              );
            })}
          </div>

          <div className="mt-10 text-center">
            <Link
              href="/servicos"
              className="inline-flex items-center gap-2 text-sm font-semibold text-brand-accent hover:underline"
            >
              Ver catálogo completo por categoria
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Como trabalhamos ─────────────────────────────────────────── */}
      <section id="como-funciona" className="py-24 sm:py-32 border-t border-border-subtle">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-14">
            <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">Do zero ao ar</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Como{" "}
              <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
                trabalhamos
              </span>
            </h2>
            <p className="text-text-secondary mt-3 max-w-xl mx-auto text-sm">
              Um processo simples e direto: você contrata a VPS, a PaperMoon faz o resto.
            </p>
          </div>

          <div className="grid sm:grid-cols-3 gap-6">
            {HOW_IT_WORKS.map((step, i) => {
              const Icon = step.icon;
              return (
                <div key={i} className="flex flex-col gap-4 p-6 rounded-2xl bg-surface-1 border border-border-subtle text-center">
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                      <Icon size={20} className="text-brand-accent" />
                    </div>
                    <span className="text-3xl font-black text-text-tertiary/25 font-mono leading-none">{step.num}</span>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-text-primary mb-2">{step.title}</h3>
                    <p className="text-xs text-text-secondary leading-relaxed">{step.description}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-10 rounded-2xl border border-border-subtle bg-surface-1 p-5 flex items-center gap-4">
            <Zap size={18} className="text-brand-accent shrink-0" />
            <p className="text-xs text-text-secondary leading-relaxed flex-1">
              Todos os serviços incluem instalação, configuração e treinamento da equipe na sua infraestrutura.
              Serviços mensais incluem suporte e manutenção contínuos.
            </p>
            <a href="#contato" className="shrink-0 text-xs font-semibold text-brand-accent hover:underline">
              Contratar →
            </a>
          </div>
        </div>
      </section>

      {/* ── Expertise de campo ───────────────────────────────────────── */}
      <section className="py-24 sm:py-32 border-t border-border-subtle">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">Além do software</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Especialistas em{" "}
              <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
                infraestrutura de ponta a ponta
              </span>
            </h2>
            <p className="text-text-secondary mt-3 max-w-xl mx-auto text-sm">
              Mais de 10 anos de experiência em campo — do cabeamento ao servidor,
              da rede ao backup. O software que gerenciamos roda sobre essa base física sólida.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {FIELD_EXPERTISE.map((area, i) => {
              const Icon = area.icon;
              return (
                <Link key={i} href={area.href} className={`rounded-2xl border p-5 flex flex-col gap-4 ${area.bg} hover:brightness-110 transition-[filter] duration-150`}>
                  <div className="w-10 h-10 rounded-xl bg-surface-0/60 flex items-center justify-center">
                    <Icon size={18} className={area.color} />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-bold text-text-primary mb-3">{area.title}</h3>
                    <ul className="space-y-2">
                      {area.items.map((item) => (
                        <li key={item} className="flex items-start gap-2 text-xs text-text-secondary">
                          <Check size={10} className={`${area.color} shrink-0 mt-0.5`} />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <p className={`text-xs font-semibold ${area.color} mt-auto`}>Ver detalhes →</p>
                </Link>
              );
            })}
          </div>

          <div className="mt-8 text-center">
            <Link
              href="/sobre"
              className="inline-flex items-center gap-2 text-sm font-semibold text-brand-accent hover:underline"
            >
              Conheça nossa história e experiência
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Logos marquee ────────────────────────────────────────────── */}
      <LogosMarquee />

      {/* ── FAQ ───────────────────────────────────────────────────────── */}
      <section id="faq" className="py-24 sm:py-32 border-t border-border-subtle">
        <div className="max-w-2xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">Dúvidas frequentes</p>
            <h2 className="text-3xl font-bold tracking-tight">Perguntas comuns</h2>
          </div>
          <LandingFAQ />
        </div>
      </section>

      {/* ── Contato ───────────────────────────────────────────────────── */}
      <section id="contato" className="py-24 sm:py-32 relative overflow-hidden border-t border-border-subtle">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-accent/10 via-surface-0 to-slate-500/10" />
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-brand-accent/12 blur-3xl rounded-full" />
        </div>
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-start">
            <div className="space-y-6">
              <div>
                <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">Vamos conversar</p>
                <h2 className="text-3xl sm:text-4xl font-black tracking-tight mb-4">
                  Conte o que sua{" "}
                  <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
                    empresa precisa
                  </span>
                </h2>
                <p className="text-text-secondary text-sm leading-relaxed">
                  Mapeamos sua operação e indicamos a solução ideal — helpdesk com GLPI, monitoramento
                  com Zabbix, virtualização com Proxmox, storage com TrueNAS ou qualquer combinação dos nossos serviços.
                </p>
              </div>

              <ul className="space-y-2">
                {[
                  "Instalação e configuração completa",
                  "Treinamento da equipe incluso em todos os serviços",
                  "Suporte contínuo nos planos mensais",
                  "Sua infraestrutura, seu controle total",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-text-secondary">
                    <Check size={14} className="text-brand-accent shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>

              <div className="space-y-3">
                <a
                  href="https://wa.me/5511999999999?text=Olá%2C%20quero%20saber%20mais%20sobre%20a%20PaperMoon"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 p-4 rounded-2xl bg-surface-1 border border-border-subtle hover:border-service-whatsapp/40 transition-colors group"
                >
                  <div className="w-10 h-10 rounded-xl bg-service-whatsapp/10 border border-service-whatsapp/20 flex items-center justify-center shrink-0">
                    <Phone size={18} className="text-service-whatsapp" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-primary group-hover:text-service-whatsapp transition-colors">WhatsApp</p>
                    <p className="text-xs text-text-tertiary mt-0.5">Resposta em até 1h útil</p>
                  </div>
                </a>

                <a
                  href="mailto:contato@papermoon.com.br"
                  className="flex items-center gap-4 p-4 rounded-2xl bg-surface-1 border border-border-subtle hover:border-brand-accent/40 transition-colors group"
                >
                  <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shrink-0">
                    <Mail size={18} className="text-brand-accent" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-primary group-hover:text-brand-accent transition-colors">E-mail direto</p>
                    <p className="text-xs text-text-tertiary mt-0.5">contato@papermoon.com.br</p>
                  </div>
                </a>
              </div>
            </div>

            <div className="rounded-2xl border border-border-subtle bg-surface-1/60 backdrop-blur-sm p-6">
              <ContactForm />
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="border-t border-border-subtle bg-surface-1/50 py-12">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10 mb-10">
            <div className="space-y-3 lg:col-span-1">
              <div className="flex items-center gap-2.5">
                <PaperMoonMark idSuffix="footer" size={24} />
                <span className="font-bold text-text-primary">PaperMoon</span>
              </div>
              <p className="text-xs text-text-tertiary leading-relaxed">
                Instalação e manutenção de ferramentas open-source na sua VPS: helpdesk, monitoramento, virtualização e comunicação.
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Navegação</p>
              <ul className="space-y-2">
                <li>
                  <Link href="/sobre" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                    Sobre
                  </Link>
                </li>
                {[
                  { label: "Serviços", href: "#servicos" },
                  { label: "Como funciona", href: "#como-funciona" },
                  { label: "FAQ", href: "#faq" },
                  { label: "Contato", href: "#contato" },
                ].map((l) => (
                  <li key={l.label}>
                    <a href={l.href} className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Serviços</p>
              <ul className="space-y-2">
                {[
                  { label: "WhatsApp API Meta", href: "/servicos/whatsapp-api" },
                  { label: "WhatsApp Evolution API", href: "/servicos/whatsapp-evolution" },
                  { label: "GLPI", href: "/servicos/glpi" },
                  { label: "Zabbix", href: "/servicos/zabbix" },
                  { label: "Proxmox VE", href: "/servicos/proxmox" },
                  { label: "TrueNAS", href: "/servicos/truenas" },
                  { label: "Nextcloud", href: "/servicos/nextcloud" },
                  { label: "AAPanel", href: "/servicos/aapanel" },
                ].map((l) => (
                  <li key={l.label}>
                    <Link href={l.href} className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Acesso</p>
              <ul className="space-y-2">
                <li>
                  <Link href="/login" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                    Entrar no painel
                  </Link>
                </li>
                <li>
                  <Link href="/login" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                    Criar conta
                  </Link>
                </li>
                <li>
                  <Link href="/forgot-password" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                    Recuperar senha
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-border-subtle flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-text-tertiary">
              © {new Date().getFullYear()} PaperMoon. Todos os direitos reservados.
            </p>
            <div className="flex gap-4 text-xs text-text-tertiary">
              <Link href="/termos" className="hover:text-text-secondary transition-colors">Termos de uso</Link>
              <span>Privacidade</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
