"use client";

import axios from "axios";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { PasswordInput } from "@/components/ui/password-input";
import { PasswordStrength } from "@/components/ui/password-strength";
import { Skeleton } from "@/components/ui/skeleton";
import { PaperMoonMark } from "@/components/common/papermoon-mark";

function AcceptInviteForm() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!token) {
    return (
      <div className="rounded-lg bg-danger-muted border border-danger/20 px-4 py-3">
        <p className="text-sm text-danger">Link de convite inválido. Solicite um novo convite ao administrador.</p>
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
      await api.post("/invitations/accept", { token, password });
      router.push("/login?invited=1");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data;
        setError(data?.error?.message ?? data?.message ?? "Convite inválido ou expirado.");
      } else {
        setError("Erro inesperado. Tente novamente.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1">
        <label htmlFor="password" className="block text-sm font-medium text-text-secondary">
          Crie sua senha
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

      <div className="space-y-1">
        <label htmlFor="confirm" className="block text-sm font-medium text-text-secondary">
          Confirmar senha
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
        <div className="rounded-lg bg-danger-muted border border-danger/20 px-3 py-2">
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}

      <Button type="submit" variant="primary" size="lg" loading={loading} className="w-full">
        Criar conta e entrar
      </Button>
    </form>
  );
}

export default function AcceptInvitePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-0">
      <div className="bg-surface-1 border border-border-default rounded-xl shadow-lg p-8 w-full max-w-sm animate-slide-up">
        <div className="flex items-center gap-3 mb-8">
          <PaperMoonMark idSuffix="invite-accept" glow size={32} />
          <div>
            <h1 className="text-lg font-bold text-text-primary">Bem-vindo à PaperMoon</h1>
            <p className="text-xs text-text-tertiary">Crie sua senha para continuar</p>
          </div>
        </div>

        <Suspense fallback={<Skeleton className="h-48 w-full rounded-lg" />}>
          <AcceptInviteForm />
        </Suspense>

        <p className="text-xs text-text-tertiary mt-4 text-center">
          Já tem conta?{" "}
          <Link href="/login" className="text-text-secondary hover:text-text-primary underline transition-colors">
            Faça login
          </Link>
        </p>
      </div>
    </div>
  );
}
