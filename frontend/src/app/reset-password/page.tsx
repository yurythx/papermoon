"use client";

import axios from "axios";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { PasswordInput } from "@/components/ui/password-input";
import { PasswordStrength } from "@/components/ui/password-strength";
import { Spinner } from "@/components/ui/spinner";
import { PaperMoonMark } from "@/components/common/papermoon-mark";
import { Shield, Zap, HeadphonesIcon, AlertCircle, CheckCircle } from "lucide-react";

const AUTH_FEATURES = [
  { icon: Shield, text: "API oficial Meta — sem risco de ban" },
  { icon: HeadphonesIcon, text: "Chatwoot multiagente provisionado em minutos" },
  { icon: Zap, text: "n8n com 400+ integrações sem código" },
];

function ResetPasswordForm() {
  const router = useRouter();
  const params = useSearchParams();
  const uid = params.get("uid") ?? "";
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!uid || !token) {
    return (
      <div className="space-y-5">
        <div className="rounded-xl bg-danger-muted border border-danger/20 px-4 py-4 flex items-start gap-3">
          <AlertCircle size={15} className="text-danger shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-danger">Link inválido</p>
            <p className="text-xs text-danger/70 mt-0.5">
              Este link de redefinição é inválido ou já expirou.
            </p>
          </div>
        </div>
        <Link href="/forgot-password">
          <Button variant="secondary" size="lg" className="w-full">
            Solicitar novo link
          </Button>
        </Link>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirm) {
      setError("As senhas não coincidem.");
      return;
    }
    if (password.length < 8) {
      setError("A senha deve ter pelo menos 8 caracteres.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/password-reset/confirm", { uid, token, password });
      router.push("/login?reset=1");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const msg = err.response?.data?.error?.message ?? err.response?.data?.message;
        setError(msg ?? "Link inválido ou expirado. Solicite um novo.");
      } else {
        setError("Erro inesperado. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="password" className="block text-sm font-medium text-text-secondary">
          Nova senha
        </label>
        <PasswordInput
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          placeholder="Mínimo 8 caracteres"
          autoComplete="new-password"
        />
        <PasswordStrength password={password} />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="confirm" className="block text-sm font-medium text-text-secondary">
          Confirmar nova senha
        </label>
        <PasswordInput
          id="confirm"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
          placeholder="Repita a senha"
          autoComplete="new-password"
        />
      </div>

      {error && (
        <div className="rounded-xl bg-danger-muted border border-danger/20 px-4 py-3 flex items-start gap-2.5">
          <AlertCircle size={15} className="text-danger shrink-0 mt-0.5" />
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}

      <Button type="submit" variant="primary" size="lg" loading={loading} className="w-full mt-2">
        Redefinir senha
      </Button>

      <Link
        href="/login"
        className="block rounded-sm pt-1 text-center text-sm text-text-tertiary hover:text-text-secondary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-0"
      >
        ← Voltar para o login
      </Link>
    </form>
  );
}

export default function ResetPasswordPage() {
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
          <PaperMoonMark idSuffix="reset-left" glow />
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

          <div className="rounded-xl border border-[rgb(var(--surface-fixed-soft)/0.10)] bg-[rgb(var(--surface-fixed-soft)/0.05)] px-4 py-3.5">
            <div className="flex items-start gap-2.5">
              <CheckCircle size={14} className="text-brand-accent shrink-0 mt-0.5" />
              <p className="text-xs leading-relaxed text-[rgb(var(--text-fixed-secondary)/0.85)]">
                Sua senha é protegida com criptografia de ponta a ponta. Nenhum dado seu é compartilhado.
              </p>
            </div>
          </div>
        </div>

        <div className="relative">
          <p className="text-xs text-[rgb(var(--text-fixed-tertiary)/0.72)]">© {new Date().getFullYear()} PaperMoon · Todos os direitos reservados</p>
        </div>
      </div>

      {/* ── Right panel — form ──────────────────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 min-h-screen">
        <div className="flex items-center gap-2.5 mb-10 lg:hidden">
          <PaperMoonMark idSuffix="reset-mobile" glow />
          <span className="text-base font-bold text-text-primary">PaperMoon</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-text-primary tracking-tight">Nova senha</h1>
            <p className="text-sm text-text-secondary mt-1.5">
              Escolha uma senha forte para proteger sua conta.
            </p>
          </div>

          <Suspense
            fallback={
              <div className="flex items-center justify-center h-48">
                <Spinner size="md" />
              </div>
            }
          >
            <ResetPasswordForm />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
