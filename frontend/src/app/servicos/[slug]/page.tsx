import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  Clock,
  Mail,
  Phone,
  AlertTriangle,
  ServerCog,
} from "lucide-react";
import { LandingNav } from "@/components/marketing/nav";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { ServiceGallery } from "@/components/marketing/service-lightbox";
import { SERVICES, getService } from "@/lib/services-content";
import { fetchCmsServicePage } from "@/lib/cms";
import { mergeService } from "@/lib/merge-service";

/* ── ISR — revalidate every 60s; on-demand via /api/revalidate ── */
export const revalidate = 60;

/* ── Static params ─────────────────────────────────────────────── */

export async function generateStaticParams(): Promise<{ slug: string }[]> {
  try {
    const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
    const res = await fetch(`${base}/api/services`, { cache: "no-store" });
    if (res.ok) {
      const slugs: string[] = await res.json();
      return slugs.map((slug) => ({ slug }));
    }
  } catch {
    // fall through to static list
  }
  return SERVICES.map((s) => ({ slug: s.slug }));
}

/* ── Metadata ──────────────────────────────────────────────────── */

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const base = getService(slug);
  if (!base) return {};
  const cms = await fetchCmsServicePage(slug);
  const svc = mergeService(base, cms);

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://app.papermoon.com.br";
  const pageUrl = `${siteUrl}/servicos/${slug}`;
  const ogImageUrl =
    `${siteUrl}/api/og?` +
    new URLSearchParams({
      title: svc.name,
      desc: svc.metaDescription,
      tag: "Serviço PaperMoon",
    }).toString();

  return {
    title: svc.metaTitle,
    description: svc.metaDescription,
    alternates: { canonical: pageUrl },
    openGraph: {
      title: svc.metaTitle,
      description: svc.metaDescription,
      url: pageUrl,
      siteName: "PaperMoon",
      type: "website",
      images: [{ url: ogImageUrl, width: 1200, height: 630, alt: svc.metaTitle }],
    },
    twitter: {
      card: "summary_large_image",
      title: svc.metaTitle,
      description: svc.metaDescription,
      images: [ogImageUrl],
    },
  };
}

/* ── FAQ item ──────────────────────────────────────────────────── */

function FAQItem({ q, a }: { q: string; a: string }) {
  return (
    <details className="group border border-border-subtle rounded-xl overflow-hidden bg-surface-1">
      <summary className="flex items-center justify-between px-6 py-4 text-sm font-medium text-text-secondary cursor-pointer list-none select-none hover:text-text-primary transition-colors gap-4">
        <span>{q}</span>
        <ChevronDown
          size={15}
          className="shrink-0 text-text-tertiary transition-transform duration-200 group-open:rotate-180"
        />
      </summary>
      <div className="px-6 pb-5">
        <p className="text-sm text-text-secondary leading-relaxed">{a}</p>
      </div>
    </details>
  );
}

/* ── Page ──────────────────────────────────────────────────────── */

export default async function ServicePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const base = getService(slug);
  if (!base) notFound();

  const cms = await fetchCmsServicePage(slug);
  const svc = mergeService(base, cms);

  const Icon = svc.icon;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://app.papermoon.com.br";
  const pageUrl = `${siteUrl}/servicos/${slug}`;

  const jsonLd = [
    svc.faqs.length > 0 && {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      mainEntity: svc.faqs.map((faq) => ({
        "@type": "Question",
        name: faq.q,
        acceptedAnswer: { "@type": "Answer", text: faq.a },
      })),
    },
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Início", item: siteUrl },
        { "@type": "ListItem", position: 2, name: "Serviços", item: `${siteUrl}/servicos` },
        { "@type": "ListItem", position: 3, name: svc.name, item: pageUrl },
      ],
    },
  ].filter(Boolean);

  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      {jsonLd.map((schema, i) => (
        <script
          key={i}
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
      ))}
      <LandingNav />

      {/* ── 1. HEPO ────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 sm:pt-32 sm:pb-20 border-b border-border-subtle overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div
            className={`absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] ${svc.colorBg} blur-3xl rounded-full opacity-60`}
          />
        </div>

        <div className="max-w-6xl mx-auto px-6">
          <Link
            href="/servicos"
            className="inline-flex items-center gap-1.5 text-xs text-text-tertiary hover:text-text-secondary transition-colors mb-8"
          >
            <ArrowLeft size={12} />
            Todos os serviços
          </Link>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              {/* Badges row */}
              <div className="flex flex-wrap items-center gap-2">
                <div
                  className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full border ${svc.colorBorder} ${svc.colorBg} ${svc.colorText} text-xs font-semibold`}
                >
                  <Icon size={12} />
                  {svc.comingSoon ? "Em breve" : "Disponível agora"}
                </div>
              </div>

              <div className="space-y-3">
                <h1 className="text-4xl sm:text-5xl font-black tracking-tight leading-[1.05]">
                  {svc.name}
                </h1>
                <p className={`text-xl font-semibold ${svc.colorText}`}>{svc.tagline}</p>
                <p className="text-base text-text-secondary leading-relaxed max-w-lg">
                  {svc.description}
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <a
                  href="#contato"
                  className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-brand-accent text-slate-950 font-semibold text-sm hover:bg-brand-accent/90 active:scale-95 transition-all shadow-xl shadow-glow-accent"
                >
                  {svc.comingSoon ? "Entrar na lista de espera" : "Falar com o time"}
                  <ArrowRight size={16} />
                </a>
              </div>
            </div>

            <div className="relative">
              {svc.heroImage ? (
                <div className="rounded-2xl overflow-hidden border border-border-default shadow-2xl ring-1 ring-white/5">
                  <Image
                    src={svc.heroImage}
                    alt={svc.heroImageAlt}
                    width={1200}
                    height={720}
                    className="w-full h-auto"
                    priority
                  />
                </div>
              ) : (
                <div
                  className={`rounded-2xl border ${svc.colorBorder} ${svc.colorBg} flex items-center justify-center aspect-video shadow-2xl`}
                >
                  <div className="flex flex-col items-center gap-4 text-center p-12">
                    <div
                      className={`w-20 h-20 rounded-2xl ${svc.colorBg} border ${svc.colorBorder} flex items-center justify-center`}
                    >
                      <Icon size={36} className={svc.colorText} />
                    </div>
                    <div>
                      <p className={`text-lg font-bold ${svc.colorText}`}>{svc.name}</p>
                      {svc.comingSoon && (
                        <p className="text-sm text-text-tertiary mt-1">
                          Screenshots disponíveis no lançamento
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. COMING SOON BANNEP (condicional) ─────────────────────── */}
      {svc.comingSoon && (
        <section className="py-6 bg-warning-muted border-b border-warning/20">
          <div className="max-w-4xl mx-auto px-6 flex items-center gap-3">
            <Clock size={16} className="text-warning shrink-0" />
            <p className="text-sm text-text-secondary">
              <strong className="text-warning">Em desenvolvimento.</strong>{" "}
              Este serviço ainda não está disponível. Entre em contato para entrar na lista de espera
              e ser avisado no lançamento.
            </p>
          </div>
        </section>
      )}

      {/* ── 3. SOBPE O SEPVIÇO ──────────────────────────────────────── */}
      <section className="py-20 sm:py-28 border-b border-border-subtle">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            {/* Texto */}
            <div className="space-y-4">
              <p
                className={`text-xs font-semibold ${svc.colorText} uppercase tracking-widest`}
              >
                Sobre o serviço
              </p>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
                O que é e como surgiu
              </h2>
              <div className="space-y-4">
                {svc.about.split("\n\n").map((paragraph, i) => (
                  <p key={i} className="text-sm text-text-secondary leading-relaxed">
                    {paragraph}
                  </p>
                ))}
              </div>
            </div>

            {/* Diferenciais */}
            <div
              className={`rounded-2xl border ${svc.colorBorder} ${svc.colorBg} p-8 space-y-5`}
            >
              <div>
                <p
                  className={`text-xs font-semibold ${svc.colorText} uppercase tracking-widest mb-2`}
                >
                  Por que escolher
                </p>
                <h3 className="text-lg font-bold text-text-primary">
                  O diferencial na prática
                </h3>
              </div>
              <ul className="space-y-3">
                {svc.differentials.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-text-secondary">
                    <div
                      className={`w-5 h-5 rounded-full ${svc.colorBg} border ${svc.colorBorder} flex items-center justify-center shrink-0 mt-0.5`}
                    >
                      <Check size={10} className={svc.colorText} />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── 4. COMO FUNCIONA ────────────────────────────────────────── */}
      <section className="py-20 sm:py-28 border-b border-border-subtle bg-surface-1/30">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <p
              className={`text-xs font-semibold ${svc.colorText} uppercase tracking-widest mb-3`}
            >
              Do zero ao funcionamento
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Como funciona na prática
            </h2>
          </div>

          <div className="grid sm:grid-cols-3 gap-5">
            {svc.steps.map((step) => (
              <div
                key={step.num}
                className="flex flex-col gap-4 p-6 rounded-2xl bg-surface-1 border border-border-subtle"
              >
                <div className="flex items-center gap-3">
                  <span className="text-3xl font-black text-text-tertiary/30 font-mono leading-none">
                    {step.num}
                  </span>
                  <div
                    className={`w-2 h-2 rounded-full ${svc.colorBg} border ${svc.colorBorder} flex items-center justify-center`}
                  >
                    <span
                      className={`w-1 h-1 rounded-full ${svc.colorText.replace("text-", "bg-")}`}
                    />
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-text-primary mb-2">{step.title}</h3>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 4. GALEPIA — sempre visível ─────────────────────────────── */}
      <section className="py-20 sm:py-28 bg-surface-1/30 border-b border-border-subtle">
        <div className="max-w-5xl mx-auto px-6 space-y-8">
          <div className="text-center">
            <p
              className={`text-xs font-semibold ${svc.colorText} uppercase tracking-widest mb-3`}
            >
              Veja em funcionamento
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Como o serviço funciona
            </h2>
            {svc.galleryImages.length > 0 && (
              <p className="text-sm text-text-tertiary mt-2">
                Clique em qualquer imagem para ampliar
              </p>
            )}
          </div>
          {svc.galleryImages.length > 0 ? (
            <ServiceGallery
              images={svc.galleryImages}
              colorBorder={svc.colorBorder}
            />
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className={`rounded-xl border ${svc.colorBorder} ${svc.colorBg} aspect-video flex flex-col items-center justify-center gap-3`}
                >
                  <div
                    className={`w-10 h-10 rounded-xl ${svc.colorBg} border ${svc.colorBorder} flex items-center justify-center`}
                  >
                    <Icon size={20} className={svc.colorText} />
                  </div>
                  <div className="text-center px-4">
                    <p className="text-xs font-medium text-text-secondary">Capturas aguardando liberação</p>
                    <p className="text-[10px] text-text-tertiary mt-0.5">
                      Imagens reais da implantação
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ── 5. FUNCIONALIDADES ──────────────────────────────────────── */}
      <section className="py-20 sm:py-28 border-b border-border-subtle">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <p
              className={`text-xs font-semibold ${svc.colorText} uppercase tracking-widest mb-3`}
            >
              O que você tem
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">Funcionalidades</h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {svc.featureGroups.map((group) => (
              <div
                key={group.title}
                className={`rounded-2xl border ${svc.colorBorder} ${svc.colorBg} p-6 space-y-4`}
              >
                <h3 className="text-sm font-bold text-text-primary">{group.title}</h3>
                <ul className="space-y-2">
                  {group.items.map((item) => (
                    <li key={item} className="flex items-start gap-2 text-xs text-text-secondary">
                      <Check size={11} className={`${svc.colorText} shrink-0 mt-0.5`} />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 6. PPÉ-PEQUISITOS TÉCNICOS ──────────────────────────────── */}
      <section className="py-20 sm:py-28 bg-surface-1/30 border-b border-border-subtle">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-10">
            <p
              className={`text-xs font-semibold ${svc.colorText} uppercase tracking-widest mb-3`}
            >
              Antes de começar
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Pré-requisitos técnicos
            </h2>
            <p className="text-sm text-text-secondary mt-3 max-w-md mx-auto">
              Verifique esses itens antes de contratar. A PaperMoon pode auxiliar na preparação do
              ambiente quando necessário.
            </p>
          </div>

          <div
            className={`rounded-2xl border ${svc.colorBorder} ${svc.colorBg} p-8`}
          >
            <div className="flex items-center gap-3 mb-6">
              <div
                className={`w-9 h-9 rounded-xl ${svc.colorBg} border ${svc.colorBorder} flex items-center justify-center shrink-0`}
              >
                <ServerCog size={18} className={svc.colorText} />
              </div>
              <p className="text-sm font-bold text-text-primary">Infraestrutura necessária</p>
            </div>
            <ul className="space-y-3">
              {svc.prerequisites.map((item, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-text-secondary">
                  <CheckCircle2
                    size={15}
                    className={`${svc.colorText} shrink-0 mt-0.5`}
                  />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── 7. O QUE É DE QUEM? ─────────────────────────────────────── */}
      <section className="py-20 sm:py-28 border-b border-border-subtle">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">O que é de quem?</h2>
            <p className="text-sm text-text-secondary mt-2 max-w-md mx-auto">
              Clareza total antes de começar.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 gap-5">
            <div
              className={`rounded-2xl border ${svc.colorBorder} ${svc.colorBg} p-6 space-y-4`}
            >
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <span
                  className={`w-5 h-5 rounded-full ${svc.colorBg} border ${svc.colorBorder} flex items-center justify-center text-[10px] font-black ${svc.colorText}`}
                >
                  P
                </span>
                PaperMoon faz
              </h3>
              <ul className="space-y-2">
                {svc.papermoonDoes.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-xs text-text-secondary">
                    <Check size={11} className={`${svc.colorText} shrink-0 mt-0.5`} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-2xl border border-warning/25 bg-warning-muted p-6 space-y-4">
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-warning/15 border border-warning/25 flex items-center justify-center text-[10px] font-black text-warning">
                  C
                </span>
                Sua responsabilidade
              </h3>
              <ul className="space-y-2">
                {svc.clientDoes.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-xs text-text-secondary">
                    <AlertTriangle size={11} className="text-warning shrink-0 mt-0.5" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-5 rounded-xl border border-border-subtle bg-surface-1 px-5 py-4 text-center">
            <p className="text-xs text-text-tertiary">
              Leia os{" "}
              <Link href="/termos" className="text-brand-accent hover:underline font-medium">
                Termos de uso completos
              </Link>{" "}
              antes de contratar.
            </p>
          </div>
        </div>
      </section>

      {/* ── 8. FAQ ──────────────────────────────────────────────────── */}
      <section className="py-20 sm:py-28 bg-surface-1/30 border-b border-border-subtle">
        <div className="max-w-2xl mx-auto px-6">
          <div className="text-center mb-10">
            <p
              className={`text-xs font-semibold ${svc.colorText} uppercase tracking-widest mb-3`}
            >
              Dúvidas
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Perguntas frequentes
            </h2>
          </div>

          {svc.faqs.length > 0 ? (
            <div className="space-y-2">
              {svc.faqs.map((faq) => (
                <FAQItem key={faq.q} q={faq.q} a={faq.a} />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-border-subtle bg-surface-1 px-6 py-8 text-center">
              <p className="text-sm text-text-tertiary">
                Ainda não temos perguntas frequentes para este serviço.{" "}
                <a href="#contato" className="text-brand-accent hover:underline font-medium">
                  Fale com nosso time
                </a>{" "}
                para tirar suas dúvidas.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* ── 9. OUTPOS SEPVIÇOS ──────────────────────────────────────── */}
      <section className="py-20 sm:py-28 border-b border-border-subtle">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-semibold text-brand-accent uppercase tracking-widest mb-3">
              Plataforma completa
            </p>
            <h2 className="text-2xl font-bold tracking-tight">Outros serviços</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {SERVICES.filter((s) => s.slug !== svc.slug).slice(0, 8).map((other) => {
              const OtherIcon = other.icon;
              return (
                <Link
                  key={other.slug}
                  href={`/servicos/${other.slug}`}
                  className={`rounded-2xl border ${other.colorBorder} ${other.colorBg} p-5 space-y-3 hover:opacity-80 transition-opacity group`}
                >
                  <div className="flex items-center justify-between">
                    <OtherIcon size={18} className={other.colorText} />
                    {other.comingSoon && (
                      <span
                        className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${other.colorBorder} ${other.colorText}`}
                      >
                        Em breve
                      </span>
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-text-primary group-hover:underline">
                      {other.name}
                    </p>
                    <p className="text-xs text-text-secondary mt-0.5 leading-relaxed line-clamp-2">
                      {other.tagline}
                    </p>
                  </div>
                </Link>
              );
            })}
          </div>
          <div className="mt-8 text-center">
            <Link
              href="/servicos"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-accent hover:underline"
            >
              {`Ver todos os ${SERVICES.length} serviços`}
              <ArrowRight size={13} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── 10. CTA + CONTATO ───────────────────────────────────────── */}
      <section id="contato" className="py-20 sm:py-28 relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-accent/10 via-surface-0 to-slate-500/10" />
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] bg-brand-accent/15 blur-3xl rounded-full" />
        </div>

        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl sm:text-4xl font-black tracking-tight mb-4">
            {svc.comingSoon ? "Entre na lista de espera" : "Pronto para começar?"}
          </h2>
          <p className="text-sm text-text-secondary max-w-md mx-auto mb-8">
            {svc.comingSoon
              ? "Seja avisado no lançamento e receba prioridade no onboarding."
              : "Fale com nosso time. Avaliamos sua operação e planejamos a configuração ideal."}
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10">
            <a
              href="mailto:contato@papermoon.com.br"
              className="flex items-center gap-3 px-6 py-4 rounded-2xl bg-surface-1 border border-border-subtle hover:border-border-default transition-colors group"
            >
              <div className="w-9 h-9 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shrink-0">
                <Mail size={16} className="text-brand-accent" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold text-text-primary group-hover:text-brand-accent transition-colors">
                  E-mail
                </p>
                <p className="text-xs text-text-tertiary">contato@papermoon.com.br</p>
              </div>
            </a>

            <a
              href="https://wa.me/5511999999999?text=Olá%2C%20quero%20saber%20mais%20sobre%20a%20PaperMoon"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-6 py-4 rounded-2xl bg-surface-1 border border-border-subtle hover:border-service-whatsapp/40 transition-colors group"
            >
              <div className="w-9 h-9 rounded-xl bg-service-whatsapp/10 border border-service-whatsapp/20 flex items-center justify-center shrink-0">
                <Phone size={16} className="text-service-whatsapp" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold text-text-primary group-hover:text-service-whatsapp transition-colors">
                  WhatsApp
                </p>
                <p className="text-xs text-text-tertiary">Pesposta em até 1h útil</p>
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* ── 11. FOOTEP MINI ─────────────────────────────────────────── */}
      <footer className="border-t border-border-subtle bg-surface-1/50 py-8">
        <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <PaperMoonMark idSuffix={`footer-${svc.slug}`} size={20} />
            <span className="text-sm font-bold text-text-primary">PaperMoon</span>
          </div>
          <div className="flex gap-5 text-xs text-text-tertiary">
            <Link href="/" className="hover:text-text-secondary transition-colors">
              Início
            </Link>
            <Link href="/termos" className="hover:text-text-secondary transition-colors">
              Termos de uso
            </Link>
            <Link href="/login" className="hover:text-text-secondary transition-colors">
              Entrar
            </Link>
          </div>
          <p className="text-xs text-text-tertiary">© {new Date().getFullYear()} PaperMoon</p>
        </div>
      </footer>
    </div>
  );
}
