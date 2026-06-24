"use client";

import axios from "axios";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Spinner } from "@/components/ui/spinner";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { Shield, Zap, HeadphonesIcon, Server, CheckCircle, AlertCircle } from "lucide-react";
import { ThemeToggle } from "@/components/ui/theme-toggle";

/* ── Left-panel feature list ────────────────────────────────────────── */

const AUTH_FEATURES = [
  { icon: Server, text: "GLPI, Zabbix, Proxmox, TrueNAS — implantados na sua VPS" },
  { icon: Shield, text: "WhatsApp via API Meta ou Evolution API com Chatwoot e n8n" },
  { icon: Zap, text: "Redes, cabeamento estruturado e manutenção de servidores" },
  { icon: HeadphonesIcon, text: "Backup automatizado com política DRP incluída" },
];

/* ── LoginForm ──────────────────────────────────────────────────────── */

function LoginForm() {
  const { login } = useAuth();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const passwordReset = params.get("reset") === "1";
  const fromInvite = params.get("invited") === "1";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        setError(data?.error?.message ?? data?.detail ?? err.message ?? "Erro ao entrar.");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Erro desconhecido. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {passwordReset && (
        <div className="rounded-xl bg-success-muted border border-success/20 px-4 py-3 flex items-start gap-2.5">
          <CheckCircle size={15} className="text-success shrink-0 mt-0.5" />
          <p className="text-sm text-success">Senha redefinida com sucesso. Faça login.</p>
        </div>
      )}
      {fromInvite && (
        <div className="rounded-xl bg-success-muted border border-success/20 px-4 py-3 flex items-start gap-2.5">
          <CheckCircle size={15} className="text-success shrink-0 mt-0.5" />
          <p className="text-sm text-success">Conta criada! Faça login para continuar.</p>
        </div>
      )}

      <div className="space-y-1.5">
        <label htmlFor="email" className="block text-sm font-medium text-text-secondary">
          E-mail
        </label>
        <Input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          placeholder="voce@empresa.com"
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label htmlFor="password" className="block text-sm font-medium text-text-secondary">
            Senha
          </label>
          <Link
            href="/forgot-password"
            className="text-xs text-text-tertiary hover:text-brand-accent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 rounded-sm"
          >
            Esqueci a senha
          </Link>
        </div>
        <PasswordInput
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
      </div>

      {error && (
        <div className="rounded-xl bg-danger-muted border border-danger/20 px-4 py-3 flex items-start gap-2.5">
          <AlertCircle size={15} className="text-danger shrink-0 mt-0.5" />
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}

      <Button type="submit" variant="primary" size="lg" disabled={loading} className="w-full mt-2">
        {loading ? "Entrando..." : "Entrar na conta"}
      </Button>
    </form>
  );
}

/* ── Page ───────────────────────────────────────────────────────────── */

export default function LoginPage() {
  return (
    <div className="min-h-screen flex bg-surface-0">

      {/* ── Left panel — branding ────────────────────────────────────── */}
      <div
        className="hidden lg:flex lg:w-[44%] relative flex-col justify-between p-12 overflow-hidden"
        style={{ backgroundColor: "rgb(var(--papermoon-midnight-fixed-rgb))" }}
      >
        {/* Glow blobs */}
        <div className="pointer-events-none absolute -top-20 -right-20 w-[480px] h-[400px] bg-brand-accent/20 blur-3xl rounded-full" />
        <div className="pointer-events-none absolute bottom-0 -left-10 w-72 h-72 bg-[rgb(var(--surface-fixed-muted)/0.12)] blur-3xl rounded-full" />
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.035]"
          style={{ backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)", backgroundSize: "28px 28px" }}
        />

        {/* Logo */}
        <div className="relative flex items-center gap-3">
          <PaperMoonMark idSuffix="auth-left" glow />
          <span className="text-base font-bold text-[rgb(var(--text-fixed-primary))] tracking-tight">PaperMoon</span>
        </div>

        {/* Main content */}
        <div className="relative space-y-10">
          <div className="space-y-4">
            <h2 className="text-3xl font-black text-[rgb(var(--text-fixed-primary))] leading-[1.1]">
              Infraestrutura de TI{" "}
              <span className="bg-gradient-to-r from-brand-accent via-warning/70 to-[rgb(var(--text-fixed-primary))] bg-clip-text text-transparent">
                gerenciada para empresas
              </span>
            </h2>
            <p className="max-w-xs text-sm leading-relaxed text-[rgb(var(--text-fixed-secondary)/0.85)]">
              Da rede física ao software open-source — GLPI, Zabbix, Proxmox, Chatwoot e mais — instalados, configurados e sob seu controle.
            </p>
          </div>

          <div className="space-y-3.5">
            {AUTH_FEATURES.map((f, i) => {
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

        </div>

        {/* Footer */}
        <div className="relative">
          <p className="text-xs text-[rgb(var(--text-fixed-tertiary)/0.72)]">© {new Date().getFullYear()} PaperMoon · Todos os direitos reservados</p>
        </div>
      </div>

      {/* ── Right panel — form ──────────────────────────────────────── */}
      <div className="flex-1 relative flex flex-col items-center justify-center p-6 min-h-screen">
        {/* Theme toggle — top right */}
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>

        {/* Mobile logo */}
        <div className="flex items-center gap-2.5 mb-10 lg:hidden">
          <PaperMoonMark idSuffix="auth-mobile" glow />
          <span className="text-base font-bold text-text-primary">PaperMoon</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">Bem-vindo de volta</h1>
            <p className="text-sm text-text-secondary mt-1.5">
              Não tem conta?{" "}
              <Link href="/register" className="font-medium text-brand-accent hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 rounded-sm">
                Criar conta
              </Link>
            </p>
          </div>

          <Suspense
            fallback={
              <div className="flex items-center justify-center h-48">
                <Spinner size="md" />
              </div>
            }
          >
            <LoginForm />
          </Suspense>
        </div>

        <div className="mt-10 flex items-center gap-6">
          <Link href="/" className="text-xs text-text-tertiary hover:text-text-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 rounded-sm">
            ← Voltar ao site
          </Link>
          <span className="text-text-tertiary text-xs">·</span>
          <Link href="/forgot-password" className="text-xs text-text-tertiary hover:text-text-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 rounded-sm">
            Esqueci a senha
          </Link>
        </div>
      </div>
    </div>
  );
}
