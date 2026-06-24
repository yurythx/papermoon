"use client";

import axios from "axios";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { Shield, Zap, HeadphonesIcon, CheckCircle, AlertCircle, Mail } from "lucide-react";

const AUTH_FEATURES = [
  { icon: Shield, text: "API oficial Meta — sem risco de ban" },
  { icon: HeadphonesIcon, text: "Chatwoot multiagente provisionado em minutos" },
  { icon: Zap, text: "n8n com 400+ integrações sem código" },
];

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/password-reset", { email });
      setSent(true);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.error?.message ?? "Erro ao enviar e-mail.");
      } else {
        setError("Erro inesperado. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-surface-0">

      {/* ── Left panel — branding ────────────────────────────────────── */}
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
          <PaperMoonMark idSuffix="forgot-left" glow />
          <span className="text-base font-bold text-[rgb(var(--text-fixed-primary))] tracking-tight">PaperMoon</span>
        </div>

        <div className="relative space-y-10">
          <div className="space-y-4">
            <h2 className="text-3xl font-black text-[rgb(var(--text-fixed-primary))] leading-[1.1]">
              Atenda no WhatsApp{" "}
              <span className="bg-gradient-to-r from-brand-accent via-warning/70 to-[rgb(var(--text-fixed-primary))] bg-clip-text text-transparent">
                do jeito certo
              </span>
            </h2>
            <p className="max-w-xs text-sm leading-relaxed text-[rgb(var(--text-fixed-secondary)/0.85)]">
              Chatwoot + API oficial Meta + n8n. Provisionado em minutos, gerenciado sem complicações.
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

        <div className="relative">
          <p className="text-xs text-[rgb(var(--text-fixed-tertiary)/0.72)]">© {new Date().getFullYear()} PaperMoon · Todos os direitos reservados</p>
        </div>
      </div>

      {/* ── Right panel — form ──────────────────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 min-h-screen">
        <div className="flex items-center gap-2.5 mb-10 lg:hidden">
          <PaperMoonMark idSuffix="forgot-mobile" glow />
          <span className="text-base font-bold text-text-primary">PaperMoon</span>
        </div>

        <div className="w-full max-w-sm">
          {sent ? (
            <div className="space-y-6 animate-slide-up">
              <div className="w-14 h-14 rounded-2xl bg-success-muted border border-success/20 flex items-center justify-center mx-auto">
                <Mail size={24} className="text-success" />
              </div>
              <div className="text-center">
                <h1 className="text-xl font-bold text-text-primary">Verifique seu e-mail</h1>
                <p className="text-sm text-text-secondary mt-2 leading-relaxed">
                  Se o endereço <strong className="text-text-primary">{email}</strong> estiver cadastrado,
                  você receberá um link em instantes. Verifique a caixa de spam.
                </p>
              </div>
              <div className="rounded-xl bg-success-muted border border-success/20 px-4 py-3 flex items-start gap-2.5">
                <CheckCircle size={15} className="text-success shrink-0 mt-0.5" />
                <p className="text-sm text-success">E-mail de redefinição enviado com sucesso.</p>
              </div>
              <Link
                href="/login"
                className="block text-center text-sm text-text-secondary hover:text-text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0 rounded-sm"
              >
                ← Voltar para o login
              </Link>
            </div>
          ) : (
            <>
              <div className="mb-8">
                <h1 className="text-2xl font-bold text-text-primary tracking-tight">Redefinir senha</h1>
                <p className="text-sm text-text-secondary mt-1.5">
                  Informe seu e-mail e enviaremos um link para criar uma nova senha.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
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

                {error && (
                  <div className="rounded-xl bg-danger-muted border border-danger/20 px-4 py-3 flex items-start gap-2.5">
                    <AlertCircle size={15} className="text-danger shrink-0 mt-0.5" />
                    <p className="text-sm text-danger">{error}</p>
                  </div>
                )}

                <Button type="submit" variant="primary" size="lg" loading={loading} className="w-full mt-2">
                  Enviar link de redefinição
                </Button>

                <Link
                  href="/login"
                  className="block rounded-sm pt-1 text-center text-sm text-text-tertiary hover:text-text-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0"
                >
                  ← Voltar para o login
                </Link>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
