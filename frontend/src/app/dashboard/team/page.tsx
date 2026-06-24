"use client";

import axios from "axios";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { teamService } from "@/lib/services";
import { useAuthStore } from "@/store/auth";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/compound/status-badge";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/compound/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Users, Pencil } from "lucide-react";
import type { Invitation, TeamMember } from "@/types";

const ROLE_LABEL: Record<string, string> = {
  owner: "Proprietário",
  admin: "Administrador",
  member: "Membro",
};

export default function TeamPage() {
  const qc = useQueryClient();
  const { me } = useAuthStore();
  const myRole = me?.role;
  const canManage = myRole === "owner" || myRole === "admin";

  const { data: members = [], isLoading: loadingMembers } = useQuery<TeamMember[]>({
    queryKey: ["team-members"],
    queryFn: teamService.listMembers,
  });

  const { data: invitations = [], isLoading: loadingInvites } = useQuery<Invitation[]>({
    queryKey: ["invitations"],
    queryFn: teamService.listInvitations,
  });

  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"admin" | "member">("member");
  const [formError, setFormError] = useState("");
  const [editingRoleFor, setEditingRoleFor] = useState<string | null>(null);

  const sendMutation = useMutation({
    mutationFn: () => teamService.sendInvitation(email, role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invitations"] });
      setEmail("");
      setRole("member");
      setFormError("");
      toast.success("Convite enviado com sucesso.");
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        setFormError(err.response?.data?.error?.message ?? "Erro ao enviar convite.");
      } else {
        setFormError("Erro inesperado.");
      }
    },
  });

  const revokeMutation = useMutation({
    mutationFn: teamService.revokeInvitation,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["invitations"] }); toast.success("Convite revogado."); },
    onError: () => toast.error("Erro ao revogar convite."),
  });

  const resendMutation = useMutation({
    mutationFn: teamService.resendInvitation,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["invitations"] }); toast.success("Convite reenviado."); },
    onError: () => toast.error("Erro ao reenviar convite."),
  });

  const changeRoleMutation = useMutation({
    mutationFn: ({ id, newRole }: { id: string; newRole: string }) =>
      teamService.changeMemberRole(id, newRole),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["team-members"] });
      setEditingRoleFor(null);
      toast.success("Papel atualizado.");
    },
    onError: () => {
      setEditingRoleFor(null);
      toast.error("Erro ao alterar papel. Verifique suas permissões.");
    },
  });

  const removeMutation = useMutation({
    mutationFn: teamService.removeMember,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["team-members"] });
      toast.success("Membro removido.");
    },
    onError: () => toast.error("Erro ao remover membro."),
  });

  const pendingInvites = invitations.filter((i) => i.status === "pending");
  const pastInvites = invitations.filter((i) => i.status !== "pending");

  return (
    <div className="space-y-8 max-w-2xl">
      <PageHeader title="Equipe" description="Membros da sua empresa e convites pendentes" />

      {/* Members list */}
      <section className="space-y-3">
        <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
          Membros ativos
        </h2>
        {loadingMembers ? (
          <div className="space-y-2">
            {[1, 2].map((i) => <Skeleton key={i} className="h-14 w-full rounded-xl" />)}
          </div>
        ) : members.length === 0 ? (
          <p className="text-sm text-text-tertiary">Nenhum membro encontrado.</p>
        ) : (
          <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
            {members.map((m) => (
              <div key={m.id} className="px-5 py-3.5 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-text-primary truncate">
                    {m.email}
                    {m.is_you && (
                      <span className="ml-2 text-xs text-text-tertiary">(você)</span>
                    )}
                  </p>
                  <p className="text-xs text-text-tertiary mt-0.5">
                    Desde {new Date(m.joined_at).toLocaleDateString("pt-BR")}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {canManage && !m.is_you && m.role !== "owner" && editingRoleFor === m.id ? (
                    <select
                      autoFocus
                      defaultValue={m.role}
                      disabled={changeRoleMutation.isPending}
                      onBlur={() => setEditingRoleFor(null)}
                      onChange={(e) => changeRoleMutation.mutate({ id: m.id, newRole: e.target.value })}
                      className="bg-surface-2 border border-border-default rounded px-2 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-brand-accent/50"
                    >
                      <option value="admin">Administrador</option>
                      <option value="member">Membro</option>
                    </select>
                  ) : (
                    <Badge variant={m.role === "owner" ? "warning" : m.role === "admin" ? "info" : "muted"}>
                      {ROLE_LABEL[m.role] ?? m.role}
                    </Badge>
                  )}
                  {canManage && !m.is_you && m.role !== "owner" && editingRoleFor !== m.id && (
                    <>
                      <button
                        onClick={() => setEditingRoleFor(m.id)}
                        title="Editar papel"
                        className="p-1 rounded text-text-tertiary hover:text-text-primary hover:bg-surface-3 transition-colors"
                      >
                        <Pencil size={13} />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Remover ${m.email} da equipe?`)) {
                            removeMutation.mutate(m.id);
                          }
                        }}
                        title="Remover membro"
                        disabled={removeMutation.isPending}
                        className="p-1 rounded text-text-tertiary hover:text-danger hover:bg-danger-muted transition-colors disabled:opacity-50"
                      >
                        <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
                          <path d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5M11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47M8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5"/>
                        </svg>
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Invite form */}
      {canManage && (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
            Convidar novo membro
          </h2>
          <div className="bg-surface-1 border border-border-subtle rounded-xl p-5 space-y-3">
            <div className="flex gap-3">
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@empresa.com"
                className="flex-1"
              />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as "admin" | "member")}
                className="bg-surface-2 border border-border-default rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-border-focus"
              >
                <option value="member">Membro</option>
                <option value="admin">Administrador</option>
              </select>
              <Button
                variant="primary"
                size="md"
                loading={sendMutation.isPending}
                disabled={!email}
                onClick={() => sendMutation.mutate()}
              >
                Convidar
              </Button>
            </div>
            {formError && <p className="text-sm text-danger">{formError}</p>}
          </div>
        </section>
      )}

      {/* Pending invitations */}
      {pendingInvites.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
            Convites pendentes ({pendingInvites.length})
          </h2>
          <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
            {pendingInvites.map((inv) => (
              <InvitationRow
                key={inv.id}
                invitation={inv}
                canRevoke={canManage}
                revoking={revokeMutation.isPending}
                onRevoke={() => revokeMutation.mutate(inv.id)}
                resending={resendMutation.isPending}
                onResend={() => resendMutation.mutate(inv.id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Past invitations */}
      {pastInvites.length > 0 && (
        <section className="space-y-3 opacity-70">
          <h2 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">
            Histórico
          </h2>
          <div className="bg-surface-1 border border-border-subtle rounded-xl divide-y divide-border-subtle overflow-hidden">
            {pastInvites.map((inv) => (
              <InvitationRow
                key={inv.id}
                invitation={inv}
                canRevoke={canManage}
                resending={resendMutation.isPending}
                onResend={() => resendMutation.mutate(inv.id)}
              />
            ))}
          </div>
        </section>
      )}

      {canManage && !loadingInvites && invitations.length === 0 && (
        <p className="text-sm text-text-tertiary">Nenhum convite enviado ainda.</p>
      )}

      {!loadingInvites && !loadingMembers && invitations.length === 0 && members.length === 0 && (
        <div className="text-center py-8">
          <Users size={28} className="text-text-tertiary mx-auto mb-2" />
          <p className="text-sm text-text-tertiary">Nenhum membro ou convite ainda.</p>
        </div>
      )}
    </div>
  );
}

function InvitationRow({
  invitation,
  canRevoke,
  revoking,
  onRevoke,
  resending,
  onResend,
}: {
  invitation: Invitation;
  canRevoke?: boolean;
  revoking?: boolean;
  onRevoke?: () => void;
  resending?: boolean;
  onResend?: () => void;
}) {
  const isExpired = invitation.status === "expired";
  const isPending = invitation.status === "pending";

  return (
    <div className="px-5 py-3.5 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-text-primary">{invitation.email}</p>
        <p className="text-xs text-text-tertiary mt-0.5">
          {ROLE_LABEL[invitation.role] ?? invitation.role}
          {(isPending || isExpired) && (
            <> · expira em {new Date(invitation.expires_at).toLocaleDateString("pt-BR")}</>
          )}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <StatusBadge status={invitation.status} />
        {canRevoke && (isPending || isExpired) && onResend && (
          <Button
            variant="ghost"
            size="xs"
            disabled={resending}
            onClick={onResend}
          >
            Reenviar
          </Button>
        )}
        {canRevoke && isPending && onRevoke && (
          <Button
            variant="ghost"
            size="xs"
            className="text-danger hover:text-danger hover:bg-danger-muted"
            disabled={revoking}
            onClick={onRevoke}
          >
            Revogar
          </Button>
        )}
      </div>
    </div>
  );
}
