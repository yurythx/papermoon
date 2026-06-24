import type { Metadata } from "next";
import Link from "next/link";
import {
  Network,
  Layers,
  Cpu,
  Archive,
  Check,
  Users,
  Award,
  Heart,
  Phone,
  Mail,
  Shield,
} from "lucide-react";
import { LandingNav } from "@/components/marketing/nav";
import { PaperMoonMark } from "@/components/common/papermoon-mark";

export const metadata: Metadata = {
  title: "Sobre a PaperMoon — 10+ anos em infraestrutura de TI",
  description:
    "Conheça a PaperMoon: mais de 10 anos de experiência em redes, cabeamento estruturado, manutenção de servidores e backup. Infraestrutura TI open-source com controle total.",
  openGraph: {
    title: "Sobre a PaperMoon — 10+ anos em infraestrutura de TI",
    description:
      "Mais de 10 anos implantando infraestrutura corporativa: redes, cabeamento, servidores e software open-source. Conheça nossa história.",
    url: "https://papermoon.com.br/sobre",
  },
};

/* ------------------------------------------------------------------ */

const SPECIALTIES = [
  {
    icon: Network,
    color: "text-info",
    bg: "bg-info-muted",
    border: "border-info/20",
    title: "Redes e conectividade",
    description:
      "Projetamos e implantamos redes corporativas do zero ou reestruturamos ambientes legados. Cada projeto começa com um levantamento detalhado das necessidades da empresa — número de usuários, segmentação por departamento, demanda de largura de banda e planos de crescimento.",
    items: [
      "Design e planejamento de redes LAN, WAN e Wi-Fi corporativo",
      "Configuração e hardening de switches gerenciáveis (L2/L3), roteadores e firewalls",
      "Segmentação de rede com VLANs por departamento ou função",
      "Implantação de VPN site-to-site e acesso remoto para equipes distribuídas",
      "Diagnóstico, troubleshooting e otimização de redes com problemas de desempenho",
      "Documentação completa da topologia e endereçamento IP",
    ],
  },
  {
    icon: Layers,
    color: "text-text-secondary",
    bg: "bg-surface-2",
    border: "border-border-subtle",
    title: "Cabeamento estruturado",
    description:
      "Realizamos projetos e instalações de cabeamento estruturado seguindo as normas técnicas brasileiras. Desde escritórios pequenos até ambientes industriais e data centers — cada cabo é certificado e documentado para garantir desempenho e rastreabilidade ao longo dos anos.",
    items: [
      "Projeto técnico de cabeamento com plantas e diagramas de passagem",
      "Instalação de cabos metálicos Cat5e, Cat6 e Cat6A certificados",
      "Cabeamento óptico com fibra monomodo e multimodo para longas distâncias",
      "Organização e identificação de racks, patch panels e DIO (distribuidor óptico)",
      "Certificação de todos os links com equipamentos Fluke Networks",
      "Conformidade com ABNT NBR 14565 e normas TIA-568",
    ],
  },
  {
    icon: Cpu,
    color: "text-warning",
    bg: "bg-warning-muted",
    border: "border-warning/20",
    title: "Manutenção de servidores e computadores",
    description:
      "Oferecemos manutenção preventiva e corretiva para toda a frota de equipamentos da empresa — de estações de trabalho a servidores físicos e virtualizados. Nosso foco é reduzir paradas não planejadas e maximizar a vida útil dos ativos de TI.",
    items: [
      "Manutenção preventiva com limpeza, troca de pasta térmica e diagnóstico de saúde",
      "Manutenção corretiva com diagnóstico e substituição de componentes defeituosos",
      "Upgrade de hardware: memória RAM, SSDs NVMe/SATA, processadores e placas",
      "Montagem de servidores bare-metal sob medida para workloads específicas",
      "Instalação e configuração de Windows Server, Windows 10/11, Ubuntu e Debian",
      "Virtualização com Proxmox VE, VMware ESXi e Hyper-V",
    ],
  },
  {
    icon: Archive,
    color: "text-success",
    bg: "bg-success-muted",
    border: "border-success/20",
    title: "Backup completo para servidores",
    description:
      "Projetamos políticas de backup corporativas seguindo a regra 3-2-1 (3 cópias, 2 mídias diferentes, 1 offsite). Não entregamos apenas a configuração — acompanhamos os primeiros ciclos de backup, executamos testes de restauração e garantimos que o plano funciona antes de encerrar o projeto.",
    items: [
      "Diagnóstico e projeto de política de backup personalizada para a empresa",
      "Backup local em NAS (TrueNAS) com ZFS e snapshots automáticos",
      "Backup em rede com replicação entre sites para disaster recovery",
      "Backup offsite integrado com provedores de nuvem (AWS S3, Backblaze B2)",
      "Agendamento automático com retenção configurável por granularidade",
      "Testes regulares de restauração para validar o DRP (Disaster Recovery Plan)",
    ],
  },
];

const VALUES = [
  {
    icon: Shield,
    title: "Fazemos o que prometemos",
    description:
      "Cada projeto entregue com documentação completa. Quando dizemos que algo funciona, você tem como verificar — logs, certificações e registros de teste inclusos.",
  },
  {
    icon: Heart,
    title: "Nos importamos com o longo prazo",
    description:
      "Não projetamos para o curto prazo. Cada decisão de infraestrutura leva em conta o crescimento da empresa nos próximos anos — evitando refações caras e migrações desnecessárias.",
  },
  {
    icon: Users,
    title: "Transferimos conhecimento",
    description:
      "Treinamos a equipe interna de TI em cada projeto. O objetivo é que você tenha autonomia — não dependência da PaperMoon para operar o dia a dia.",
  },
];

/* ------------------------------------------------------------------ */

export default function SobrePage() {
  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      <LandingNav />

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative pt-32 pb-20 sm:pt-40 sm:pb-28 overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-gradient-to-b from-brand-accent/15 via-brand-accent/8 to-transparent blur-3xl rounded-full" />
          <div
            className="absolute inset-0 opacity-[0.02]"
            style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "32px 32px" }}
          />
        </div>

        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-brand-accent/30 bg-brand-accent/10 text-brand-accent text-xs font-semibold mb-6">
            <Award size={12} />
            Mais de 10 anos de experiência em infraestrutura de TI
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-[1.05] mb-6">
            Infraestrutura de TI{" "}
            <span className="bg-gradient-to-r from-brand-accent via-warning/70 to-text-primary bg-clip-text text-transparent">
              feita com propriedade
            </span>
          </h1>

          <p className="text-base sm:text-lg text-text-secondary leading-relaxed max-w-2xl mx-auto mb-10">
            A PaperMoon nasceu da prática de campo: mais de uma década instalando redes, certificando
            cabeamentos, mantendo servidores e estruturando backups para empresas de todos os portes.
            O software open-source que gerenciamos é construído sobre essa base física sólida.
          </p>

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-5 max-w-2xl mx-auto">
            {[
              { value: "10+", label: "Anos de experiência" },
              { value: "4", label: "Especialidades técnicas" },
              { value: "100%", label: "Open-source" },
              { value: "∞", label: "Suporte incluso" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-2xl bg-surface-1 border border-border-subtle p-4 text-center">
                <p className="text-2xl sm:text-3xl font-black text-text-primary mb-1">{stat.value}</p>
                <p className="text-[11px] text-text-tertiary leading-tight">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Nossa história ───────────────────────────────────────────── */}
      <section className="py-20 sm:py-24 border-t border-border-subtle">
        <div className="max-w-3xl mx-auto px-6">
          <div className="space-y-5 text-sm text-text-secondary leading-relaxed">
            <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest">Nossa história</p>
            <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
              Começamos no campo. Continuamos no campo.
            </h2>
            <p>
              Há mais de 10 anos a PaperMoon trabalha com infraestrutura de TI para empresas —
              primeiro como equipe de suporte técnico presencial, passando cabo por cabo, configurando
              switches e mantendo servidores físicos em data centers e salas de TI pelo Brasil.
            </p>
            <p>
              Com o tempo, percebemos que a maioria das empresas enfrenta o mesmo problema: ferramentas
              de gestão excelentes existem (GLPI, Zabbix, Proxmox, Chatwoot), mas são difíceis de
              implantar e manter sem uma equipe técnica dedicada. Surgiu a PaperMoon como a conhecemos hoje
              — uma empresa que une a experiência de campo com a gestão de software open-source.
            </p>
            <p>
              Hoje gerenciamos toda a pilha de TI do cliente: da tomada ao servidor, do cabeamento ao
              backup automatizado, da rede ao atendimento ao cliente via WhatsApp.
              Você tem uma equipe de TI disponível sem precisar contratar uma internamente.
            </p>
          </div>
        </div>
      </section>

      {/* ── Especialidades ───────────────────────────────────────────── */}
      <section className="py-24 sm:py-32 border-t border-border-subtle bg-surface-1/30">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">Expertise técnica</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Nossas{" "}
              <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
                especialidades
              </span>
            </h2>
            <p className="text-text-secondary mt-3 max-w-xl mx-auto text-sm">
              Cada área é resultado de anos de trabalho em campo — não de certificações teóricas.
            </p>
          </div>

          <div className="space-y-8">
            {SPECIALTIES.map((spec, i) => {
              const Icon = spec.icon;
              return (
                <div
                  key={i}
                  className={`rounded-2xl border ${spec.border} ${spec.bg} p-7 sm:p-8`}
                >
                  <div className="flex flex-col sm:flex-row gap-6">
                    <div className="shrink-0">
                      <div className="w-12 h-12 rounded-2xl bg-surface-0/60 border border-border-subtle flex items-center justify-center">
                        <Icon size={22} className={spec.color} />
                      </div>
                    </div>
                    <div className="flex-1 space-y-4">
                      <div>
                        <h3 className="text-lg font-bold text-text-primary mb-2">{spec.title}</h3>
                        <p className="text-sm text-text-secondary leading-relaxed">{spec.description}</p>
                      </div>
                      <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-2">
                        {spec.items.map((item) => (
                          <li key={item} className="flex items-start gap-2 text-xs text-text-secondary">
                            <Check size={12} className={`${spec.color} shrink-0 mt-0.5`} />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Nossos valores ───────────────────────────────────────────── */}
      <section className="py-24 sm:py-32 border-t border-border-subtle">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-14">
            <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">Como trabalhamos</p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
              Nossa{" "}
              <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
                abordagem
              </span>
            </h2>
          </div>

          <div className="grid sm:grid-cols-3 gap-6">
            {VALUES.map((val, i) => {
              const Icon = val.icon;
              return (
                <div key={i} className="p-6 rounded-2xl bg-surface-1 border border-border-subtle space-y-3">
                  <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                    <Icon size={18} className="text-brand-accent" />
                  </div>
                  <h3 className="text-sm font-bold text-text-primary">{val.title}</h3>
                  <p className="text-xs text-text-secondary leading-relaxed">{val.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section className="py-24 sm:py-32 relative overflow-hidden border-t border-border-subtle">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-accent/8 via-surface-0 to-slate-500/8" />
        </div>
        <div className="max-w-3xl mx-auto px-6 text-center space-y-6">
          <h2 className="text-3xl sm:text-4xl font-black tracking-tight">
            Pronto para ter uma{" "}
            <span className="bg-gradient-to-r from-brand-accent to-text-primary bg-clip-text text-transparent">
              infraestrutura sólida?
            </span>
          </h2>
          <p className="text-text-secondary text-sm leading-relaxed max-w-xl mx-auto">
            Conte como é a infraestrutura atual da sua empresa e o que você precisa. Nossa equipe
            mapeia os pontos críticos e indica a solução mais adequada — sem jargões, sem pressão.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="https://wa.me/5511999999999?text=Olá%2C%20quero%20saber%20mais%20sobre%20a%20PaperMoon"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-brand-accent text-slate-950 font-semibold text-sm hover:bg-brand-accent/90 active:scale-95 transition-all shadow-xl shadow-glow-accent"
            >
              <Phone size={15} />
              Falar no WhatsApp
            </a>
            <a
              href="mailto:contato@papermoon.com.br"
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-surface-2 border border-border-default text-text-primary font-semibold text-sm hover:bg-surface-3 hover:border-border-focus transition-all"
            >
              <Mail size={15} />
              contato@papermoon.com.br
            </a>
          </div>

          <p className="text-xs text-text-tertiary pt-2">
            Ou{" "}
            <Link href="/" className="text-brand-accent hover:underline font-medium">
              veja nossos serviços
            </Link>{" "}
            e{" "}
            <Link href="/#contato" className="text-brand-accent hover:underline font-medium">
              preencha o formulário de contato
            </Link>
          </p>
        </div>
      </section>

      {/* ── Footer simples ───────────────────────────────────────────── */}
      <footer className="border-t border-border-subtle bg-surface-1/50 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <PaperMoonMark idSuffix="sobre-footer" size={20} />
            <span className="text-sm font-bold text-text-primary">PaperMoon</span>
          </div>

          <div className="flex items-center gap-6">
            <Link href="/" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
              Início
            </Link>
            <Link href="/#servicos" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
              Serviços
            </Link>
            <Link href="/#contato" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
              Contato
            </Link>
            <Link href="/login" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
              Entrar
            </Link>
          </div>

          <p className="text-xs text-text-tertiary">
            © {new Date().getFullYear()} PaperMoon
          </p>
        </div>
      </footer>
    </div>
  );
}
