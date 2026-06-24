"use client";

import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuthStore } from "@/store/auth";
import { authService } from "@/lib/services";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Spinner } from "@/components/ui/spinner";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { AlertCircle, Shield, Server, Zap, HeadphonesIcon } from "lucide-react";
import { api } from "@/lib/api";

/* ── Left-panel feature list ────────────────────────────────────────── */

const FEATURES = [
  { icon: Server, text: "GLPI, Zabbix, Proxmox, TrueNAS — na sua VPS" },
  { icon: Shield, text: "WhatsApp via API Meta com Chatwoot e n8n" },
  { icon: Zap, text: "Redes, cabeamento e manutenção de servidores" },
  { icon: HeadphonesIcon, text: "Suporte contínuo e treinamento da equipe" },
];

/* ── RegisterForm ───────────────────────────────────────────────────── */

export default function RegisterPage() {
  const router = useRouter();
  const { setMe } = useAuthStore();

  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    company_name: "",
    email: "",
    phone: "",
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function set(field: string) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (form.password !== form.confirm_password) {
      setError("As senhas não conferem.");
      return;
    }
    if (form.password.length < 8) {
      setError("A senha deve ter ao menos 8 caracteres.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/register", {
        first_name: form.first_name,
        last_name: form.last_name,
        company_name: form.company_name,
        email: form.email,
        phone: form.phone,
        password: form.password,
      });

      // Fetch the user session that was set via httpOnly cookie
      const me = await authService.me();
      setMe(me);
      router.replace("/onboarding");
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        const details = data?.error?.details;
        if (Array.isArray(details) && details.length > 0) {
          setError(details.join(" "));
        } else {
          setError(data?.error?.message ?? data?.detail ?? "Erro ao criar conta.");
        }
      } else {
        setError("Erro desconhecido. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-surface-0">

      {/* ── Left panel ─────────────────────────────────────────────── */}
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
          <PaperMoonMark idSuffix="register-left" glow />
          <span className="text-base font-bold text-[rgb(var(--text-fixed-primary))] tracking-tight">PaperMoon</span>
        </div>

        <div className="relative space-y-10">
          <div className="space-y-4">
            <h2 className="text-3xl font-black text-[rgb(var(--text-fixed-primary))] leading-[1.1]">
              Infraestrutura de TI{" "}
              <span className="bg-gradient-to-r from-brand-accent via-warning/70 to-[rgb(var(--text-fixed-primary))] bg-clip-text text-transparent">
                gerenciada para empresas
              </span>
            </h2>
            <p className="max-w-xs text-sm leading-relaxed text-[rgb(var(--text-fixed-secondary)/0.85)]">
              Crie sua conta em 30 segundos. Nossa equipe entrará em contato para configurar seus serviços.
            </p>
          </div>

          <div className="space-y-3.5">
            {FEATURES.map((f, i) => {
              const Icon = f.icon;
              return (
                <div key={i} className="flex items-center gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[rgb(var(--surface-fixed-soft)/0.10)] bg-[rgb(var(--surface-fixed-soft)/0.08)]">
                    <Icon size={14} className="text-brand-accent" />
                  </div>
                  <span className="text-sm text-[rgb(var(--text-fixed-secondary)/0.80)]">{f.text}</span>
                </div>
              );
            })}
          </div>

          <div className="rounded-xl border border-[rgb(var(--surface-fixed-soft)/0.10)] bg-[rgb(var(--surface-fixed-soft)/0.05)] px-4 py-3.5">
            <p className="text-xs leading-relaxed text-[rgb(var(--text-fixed-secondary)/0.85)]">
              &ldquo;A PaperMoon configurou toda a nossa infraestrutura em dois dias. Suporte incrível.&rdquo;
            </p>
            <p className="mt-1.5 text-[11px] text-[rgb(var(--text-fixed-tertiary)/0.80)]">— Cliente PaperMoon</p>
          </div>
        </div>

        <div className="relative">
          <p className="text-xs text-[rgb(var(--text-fixed-tertiary)/0.72)]">© {new Date().getFullYear()} PaperMoon · Todos os direitos reservados</p>
        </div>
      </div>

      {/* ── Right panel ─────────────────────────────────────────────── */}
      <div className="flex-1 relative flex flex-col items-center justify-center p-6 min-h-screen">
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>

        {/* Mobile logo */}
        <div className="flex items-center gap-2.5 mb-8 lg:hidden">
          <PaperMoonMark idSuffix="register-mobile" glow />
          <span className="text-base font-bold text-text-primary">PaperMoon</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-7">
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">Criar conta</h1>
            <p className="text-sm text-text-secondary mt-1.5">
              Já tem conta?{" "}
              <Link href="/login" className="font-medium text-brand-accent hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 rounded-sm">
                Entrar
              </Link>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name row */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label htmlFor="first_name" className="block text-sm font-medium text-text-secondary">
                  Nome
                </label>
                <Input
                  id="first_name"
                  value={form.first_name}
                  onChange={set("first_name")}
                  required
                  autoComplete="given-name"
                  placeholder="João"
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="last_name" className="block text-sm font-medium text-text-secondary">
                  Sobrenome
                </label>
                <Input
                  id="last_name"
                  value={form.last_name}
                  onChange={set("last_name")}
                  required
                  autoComplete="family-name"
                  placeholder="Silva"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="company_name" className="block text-sm font-medium text-text-secondary">
                Nome da empresa
              </label>
              <Input
                id="company_name"
                value={form.company_name}
                onChange={set("company_name")}
                required
                autoComplete="organization"
                placeholder="Empresa Ltda."
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-medium text-text-secondary">
                E-mail profissional
              </label>
              <Input
                id="email"
                type="email"
                value={form.email}
                onChange={set("email")}
                required
                autoComplete="email"
                placeholder="voce@empresa.com"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="phone" className="block text-sm font-medium text-text-secondary">
                Telefone / WhatsApp <span className="text-text-tertiary">(opcional)</span>
              </label>
              <Input
                id="phone"
                type="tel"
                value={form.phone}
                onChange={set("phone")}
                autoComplete="tel"
                placeholder="(11) 99999-9999"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-sm font-medium text-text-secondary">
                Senha <span className="text-text-tertiary text-xs">(mín. 8 caracteres)</span>
              </label>
              <PasswordInput
                id="password"
                value={form.password}
                onChange={set("password")}
                required
                autoComplete="new-password"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="confirm_password" className="block text-sm font-medium text-text-secondary">
                Confirmar senha
              </label>
              <PasswordInput
                id="confirm_password"
                value={form.confirm_password}
                onChange={set("confirm_password")}
                required
                autoComplete="new-password"
              />
            </div>

            {error && (
              <div className="rounded-xl bg-danger-muted border border-danger/20 px-4 py-3 flex items-start gap-2.5">
                <AlertCircle size={15} className="text-danger shrink-0 mt-0.5" />
                <p className="text-sm text-danger">{error}</p>
              </div>
            )}

            <Button type="submit" variant="primary" size="lg" disabled={loading} className="w-full mt-2">
              {loading ? (
                <span className="flex items-center gap-2">
                  <Spinner size="xs" />
                  Criando conta…
                </span>
              ) : (
                "Criar conta grátis"
              )}
            </Button>

            <p className="text-[11px] text-text-tertiary text-center leading-relaxed">
              Ao criar uma conta você concorda com os{" "}
              <Link href="/termos" className="underline hover:text-text-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 rounded-sm">
                Termos de uso
              </Link>
              .
            </p>
          </form>
        </div>

        <div className="mt-8 flex items-center gap-6">
          <Link href="/" className="text-xs text-text-tertiary hover:text-text-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 rounded-sm">
            ← Voltar ao site
          </Link>
        </div>
      </div>
    </div>
  );
}
