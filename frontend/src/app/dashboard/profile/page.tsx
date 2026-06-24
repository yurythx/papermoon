"use client";

import axios from "axios";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { authService, customerService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/compound/status-badge";
import { PageHeader } from "@/components/compound/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { PasswordStrength } from "@/components/ui/password-strength";

export default function ProfilePage() {
  const queryClient = useQueryClient();

  const { data: customer, isLoading } = useQuery({
    queryKey: ["customer-me"],
    queryFn: customerService.getMe,
  });

  const [companyName, setCompanyName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const updateMutation = useMutation({
    mutationFn: (name: string) => customerService.updateMe({ company_name: name }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["customer-me"], updated);
      toast.success("Dados salvos com sucesso.");
    },
    onError: () => toast.error("Erro ao salvar."),
  });

  const passwordMutation = useMutation({
    mutationFn: () => authService.changePassword(currentPassword, newPassword),
    onSuccess: () => {
      toast.success("Senha alterada com sucesso.");
      setCurrentPassword(""); setNewPassword(""); setConfirmPassword(""); setPasswordError("");
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        setPasswordError(err.response?.data?.error?.message ?? "Erro ao alterar senha.");
      } else {
        setPasswordError("Erro inesperado.");
      }
    },
  });

  function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPasswordError("");
    if (newPassword !== confirmPassword) return setPasswordError("As senhas não coincidem.");
    if (newPassword.length < 8) return setPasswordError("Mínimo 8 caracteres.");
    passwordMutation.mutate();
  }

  if (isLoading) {
    return (
      <div className="max-w-lg space-y-8">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
    );
  }

  const displayName = companyName || customer?.company_name || "";

  return (
    <div className="space-y-8 max-w-lg">
      <PageHeader title="Minha empresa" description="Dados cadastrais e segurança da conta" />

      {/* Company data */}
      <div className="bg-surface-1 border border-border-subtle rounded-xl p-6 space-y-5">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
          Dados cadastrais
        </h2>

        <div className="space-y-1">
          <label htmlFor="company_name" className="block text-sm font-medium text-text-secondary">
            Razão social
          </label>
          <Input
            id="company_name"
            type="text"
            defaultValue={customer?.company_name}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="Nome da empresa"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="document" className="block text-sm font-medium text-text-secondary">
            CNPJ
          </label>
          <Input
            id="document"
            type="text"
            value={customer?.document ?? ""}
            readOnly
            className="opacity-60 cursor-not-allowed"
          />
        </div>

        <div className="space-y-1">
          <span className="block text-sm font-medium text-text-secondary">Status</span>
          {customer?.status && <StatusBadge status={customer.status} />}
        </div>

        <Button
          variant="primary"
          size="sm"
          loading={updateMutation.isPending}
          disabled={!companyName || companyName === customer?.company_name}
          onClick={() => updateMutation.mutate(displayName)}
        >
          Salvar alterações
        </Button>
      </div>

      {/* Change password */}
      <div className="bg-surface-1 border border-border-subtle rounded-xl p-6">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-5">
          Alterar senha
        </h2>
        <form onSubmit={handlePasswordSubmit} noValidate className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="current_password" className="block text-sm font-medium text-text-secondary">
              Senha atual
            </label>
            <PasswordInput
              id="current_password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="new_password" className="block text-sm font-medium text-text-secondary">
              Nova senha
            </label>
            <PasswordInput
              id="new_password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              placeholder="Mínimo 8 caracteres"
            />
            <PasswordStrength password={newPassword} />
          </div>
          <div className="space-y-1">
            <label htmlFor="confirm_password" className="block text-sm font-medium text-text-secondary">
              Confirmar nova senha
            </label>
            <PasswordInput
              id="confirm_password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
              placeholder="Repita a nova senha"
            />
          </div>

          {passwordError && (
            <div className="rounded-lg bg-danger-muted border border-danger/20 px-3 py-2">
              <p className="text-sm text-danger">{passwordError}</p>
            </div>
          )}

          <Button
            type="submit"
            variant="secondary"
            size="sm"
            loading={passwordMutation.isPending}
            disabled={!currentPassword || !newPassword || !confirmPassword}
          >
            Alterar senha
          </Button>
        </form>
      </div>
    </div>
  );
}
