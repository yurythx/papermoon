"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import { authService } from "@/lib/services";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { Mail, LayoutDashboard, ExternalLink, LogOut } from "lucide-react";

const STEPS = [
  { n: 1, label: "Cadastro recebido", done: true },
  { n: 2, label: "Configuração da empresa", done: false },
  { n: 3, label: "Acesso ao dashboard", done: false },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { me, setMe, clearMe } = useAuthStore();

  // Poll /auth/me every 10s — as soon as admin provisions the customer,
  // the response will include `customer` and this page auto-redirects.
  const { isFetching } = useQuery({
    queryKey: ["onboarding-me-poll"],
    queryFn: async () => {
      const data = await authService.me();
      setMe(data);
      return data;
    },
    refetchInterval: 10_000,
    refetchIntervalInBackground: false,
    staleTime: 0,
  });

  useEffect(() => {
    if (me?.customer) router.replace("/dashboard");
    if (me?.user?.is_staff) router.replace("/backoffice");
  }, [me, router]);

  function logout() {
    authService.logout().finally(() => {
      clearMe();
      router.push("/login");
    });
  }

  // Admin users are redirected above; this page is for client users without a customer yet
  return (
    <div className="min-h-screen flex bg-surface-0">

      {/* ── Left panel ────────────────────────────────────────────── */}
      <div
        className="hidden lg:flex lg:w-[44%] relative flex-col justify-between p-12 overflow-hidden"
        style={{ backgroundColor: "rgb(var(--papermoon-midnight-fixed-rgb))" }}
      >
        <div className="pointer-events-none absolute -top-20 -right-20 w-[480px] h-[400px] bg-brand-accent/20 blur-3xl rounded-full" />
        <div className="pointer-events-none absolute bottom-0 -left-10 w-72 h-72 bg-[rgb(var(--surface-fixed-muted)/0.12)] blur-3xl rounded-full" />
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.035]"
          style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "28px 28px" }}
        />

        <div className="relative flex items-center gap-3">
          <PaperMoonMark idSuffix="onboarding-left" glow />
          <span className="text-base font-bold text-[rgb(var(--text-fixed-primary))] tracking-tight">PaperMoon</span>
        </div>

        <div className="relative space-y-10">
          <div className="space-y-4">
            <h2 className="text-3xl font-black text-[rgb(var(--text-fixed-primary))] leading-[1.1]">
              Tudo pronto{" "}
              <span className="bg-gradient-to-r from-brand-accent via-warning/70 to-[rgb(var(--text-fixed-primary))] bg-clip-text text-transparent">
                em minutos
              </span>
            </h2>
            <p className="max-w-xs text-sm leading-relaxed text-[rgb(var(--text-fixed-secondary)/0.85)]">
              Nossa equipe implanta os serviços contratados — software open-source, redes ou infraestrutura física.
              Você mantém controle total do ambiente.
            </p>
          </div>

          {/* Progress steps */}
          <div className="space-y-3">
            {STEPS.map((step) => (
              <div key={step.n} className="flex items-center gap-3">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold
                  ${step.done
                    ? "bg-brand-accent text-[rgb(var(--papermoon-midnight-fixed-rgb))]"
                    : "border border-[rgb(var(--surface-fixed-soft)/0.15)] bg-[rgb(var(--surface-fixed-soft)/0.08)] text-[rgb(var(--text-fixed-disabled)/0.45)]"
                  }`}>
                  {step.done ? "✓" : step.n}
                </div>
                <span className={`text-sm ${step.done ? "text-[rgb(var(--text-fixed-secondary)/0.80)]" : "text-[rgb(var(--text-fixed-disabled)/0.40)]"}`}>
                  {step.label}
                </span>
              </div>
            ))}
          </div>

          {/* Social proof */}
          <div className="rounded-xl border border-[rgb(var(--surface-fixed-soft)/0.10)] bg-[rgb(var(--surface-fixed-soft)/0.05)] px-4 py-3.5">
            <p className="text-xs leading-relaxed text-[rgb(var(--text-fixed-secondary)/0.85)]">
              &ldquo;A PaperMoon montou toda a nossa infraestrutura — rede, cabeamento e GLPI — em dois dias. Suporte incrível.&rdquo;
            </p>
            <p className="mt-1.5 text-[11px] text-[rgb(var(--text-fixed-tertiary)/0.80)]">— Cliente PaperMoon</p>
          </div>
        </div>

        <div className="relative">
          <p className="text-xs text-[rgb(var(--text-fixed-tertiary)/0.72)]">© {new Date().getFullYear()} PaperMoon · Todos os direitos reservados</p>
        </div>
      </div>

      {/* ── Right panel ───────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 min-h-screen">
        {/* Mobile logo */}
        <div className="flex items-center gap-2.5 mb-10 lg:hidden">
          <PaperMoonMark idSuffix="onboarding-mobile" glow />
          <span className="text-base font-bold text-text-primary">PaperMoon</span>
        </div>

        <div className="w-full max-w-sm space-y-8">
          {/* Icon */}
          <div className="flex flex-col items-center text-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-brand-accent/12 border border-brand-accent/25 flex items-center justify-center">
              <Mail size={28} className="text-brand-accent" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-text-primary tracking-tight">
                Aguardando configuração
              </h1>
              <p className="text-sm text-text-secondary mt-2 leading-relaxed">
                Sua conta foi criada com sucesso. Nossa equipe está configurando
                seus serviços e enviará um e-mail assim que estiver pronto.
              </p>
            </div>
          </div>

          {/* What happens next */}
          <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle">
            <div className="px-4 py-3 flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-brand-accent/15 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-[10px] font-bold text-brand-accent">1</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">Verifique seu e-mail</p>
                <p className="text-xs text-text-secondary mt-0.5">
                  Você receberá um link de ativação com os dados de acesso.
                </p>
              </div>
            </div>
            <div className="px-4 py-3 flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-brand-accent/15 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-[10px] font-bold text-brand-accent">2</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">Instalação na sua VPS</p>
                <p className="text-xs text-text-secondary mt-0.5">
                  Nossa equipe realiza a implantação dos serviços contratados — software na sua VPS ou infraestrutura física no local.
                </p>
              </div>
            </div>
            <div className="px-4 py-3 flex items-start gap-3">
              <div className="w-6 h-6 rounded-full bg-brand-accent/15 flex items-center justify-center shrink-0 mt-0.5">
                <span className="text-[10px] font-bold text-brand-accent">3</span>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">Acesse o dashboard</p>
                <p className="text-xs text-text-secondary mt-0.5">
                  Gerencie seus serviços, faturas e chaves de API em um só lugar.
                </p>
              </div>
            </div>
          </div>

          {/* Responsibilities notice */}
          <div className="rounded-xl border border-warning/25 bg-warning-muted px-4 py-4 space-y-2">
            <p className="text-xs font-semibold text-warning">Suas responsabilidades</p>
            <ul className="space-y-1.5">
              {[
                "Contratar e manter ativa a VPS (para serviços de software)",
                "Fornecer acesso SSH ou acesso físico ao local conforme o serviço",
                "Manter backups dos dados armazenados no servidor",
                "Cumprir os termos de uso de plataformas de terceiros (Meta, etc.)",
              ].map((item) => (
                <li key={item} className="flex items-start gap-1.5 text-xs text-text-secondary">
                  <span className="text-warning shrink-0 mt-px">·</span>
                  {item}
                </li>
              ))}
            </ul>
            <p className="text-[11px] text-text-tertiary pt-1">
              Leia os{" "}
              <Link href="/termos" className="text-brand-accent hover:underline">Termos de uso</Link>
              {" "}antes de prosseguir.
            </p>
          </div>

          {/* Polling indicator */}
          <div className="flex items-center justify-center gap-2 text-xs text-text-tertiary">
            {isFetching ? (
              <>
                <Spinner size="xs" />
                <span>Verificando status…</span>
              </>
            ) : (
              <span>Verificação automática a cada 10 segundos</span>
            )}
          </div>

          {/* CTAs */}
          <div className="space-y-3">
            <Link href="/dashboard">
              <Button variant="secondary" size="lg" className="w-full">
                <LayoutDashboard size={14} className="mr-1.5" />
                Tentar acessar o dashboard
              </Button>
            </Link>
            <a
              href="https://papermoon.com.br/suporte"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-1.5 text-sm text-text-tertiary hover:text-text-secondary transition-colors"
            >
              <ExternalLink size={12} />
              Precisa de ajuda? Fale com o suporte
            </a>
          </div>

          <button
            onClick={logout}
            className="flex items-center gap-1.5 text-xs text-text-tertiary hover:text-text-secondary transition-colors mx-auto"
          >
            <LogOut size={11} />
            Sair da conta
          </button>
        </div>
      </div>
    </div>
  );
}
