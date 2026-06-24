"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { notificationService } from "@/lib/services";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/compound/page-header";
import {
  Bell,
  Check,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Server,
  RefreshCw,
  UserCheck,
  UserX,
  Mail,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { InAppNotification } from "@/types";

type Variant = "success" | "danger" | "warning" | "info";

const EVENT_META: Record<string, { variant: Variant; icon: LucideIcon }> = {
  "payment.processed":          { variant: "success", icon: CheckCircle2 },
  "payment.failed":             { variant: "danger",  icon: XCircle },
  "payment.due_soon":           { variant: "warning", icon: AlertTriangle },
  "payment.dunning_d3":         { variant: "danger",  icon: XCircle },
  "subscription.created":       { variant: "success", icon: CheckCircle2 },
  "subscription.renewed":       { variant: "success", icon: RefreshCw },
  "subscription.suspended":     { variant: "warning", icon: AlertTriangle },
  "subscription.expired":       { variant: "danger",  icon: XCircle },
  "subscription.expiring_soon": { variant: "warning", icon: AlertTriangle },
  "subscription.grace_period":  { variant: "warning", icon: AlertTriangle },
  "subscription.plan_changed":  { variant: "info",    icon: Info },
  "subscription.cancelled":     { variant: "danger",  icon: XCircle },
  "service.provisioned":        { variant: "success", icon: Server },
  "customer.suspended":         { variant: "danger",  icon: UserX },
  "customer.reactivated":       { variant: "success", icon: UserCheck },
  "invitation.created":         { variant: "info",    icon: Mail },
  "invitation.accepted":        { variant: "success", icon: UserCheck },
};

const variantIcon: Record<Variant, string> = {
  success: "text-success",
  danger:  "text-danger",
  warning: "text-warning",
  info:    "text-info",
};

const variantBg: Record<Variant, string> = {
  success: "bg-success/10",
  danger:  "bg-danger/10",
  warning: "bg-warning/10",
  info:    "bg-info/10",
};

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["notifications-page", page],
    queryFn: () => notificationService.list(page),
  });

  function invalidateAll() {
    queryClient.invalidateQueries({ queryKey: ["notifications-page"] });
    queryClient.invalidateQueries({ queryKey: ["notifications-bell"] });
  }

  const markRead = useMutation({
    mutationFn: notificationService.markRead,
    onSuccess: invalidateAll,
  });

  const markAllRead = useMutation({
    mutationFn: notificationService.markAllRead,
    onSuccess: () => { toast.success("Todas marcadas como lidas."); invalidateAll(); },
  });

  const notifications = data?.results ?? [];
  const numPages = data?.num_pages ?? 1;
  const unreadCount = data?.unread_count ?? 0;

  return (
    <div className="space-y-8 max-w-2xl">
      <PageHeader
        title="Notificações"
        description={unreadCount > 0 ? `${unreadCount} não lida${unreadCount !== 1 ? "s" : ""}` : "Tudo em dia"}
        actions={
          unreadCount > 0 ? (
            <Button
              variant="ghost"
              size="sm"
              loading={markAllRead.isPending}
              onClick={() => markAllRead.mutate()}
            >
              <Check size={14} />
              Marcar todas como lidas
            </Button>
          ) : undefined
        }
      />

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-surface-1 border border-border-subtle rounded-xl p-4 flex gap-3">
              <Skeleton className="w-8 h-8 rounded-full shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-3 w-1/3" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            </div>
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-16">
          <Bell size={32} className="text-text-tertiary mx-auto mb-3" />
          <p className="text-sm font-medium text-text-primary mb-1">Tudo em dia!</p>
          <p className="text-xs text-text-secondary">Nenhuma notificação pendente.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <NotificationRow
              key={n.id}
              notification={n}
              onMarkRead={() => markRead.mutate(n.id)}
              markingRead={markRead.isPending && markRead.variables === n.id}
            />
          ))}
        </div>
      )}

      {numPages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <Button
            variant="secondary"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            ← Anterior
          </Button>
          <span className="text-sm text-text-tertiary">{page} / {numPages}</span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page === numPages}
            onClick={() => setPage((p) => Math.min(numPages, p + 1))}
          >
            Próxima →
          </Button>
        </div>
      )}
    </div>
  );
}

function NotificationRow({
  notification: n,
  onMarkRead,
  markingRead,
}: {
  notification: InAppNotification;
  onMarkRead: () => void;
  markingRead: boolean;
}) {
  const meta = EVENT_META[n.event_type] ?? { variant: "info" as Variant, icon: Info };
  const Icon = meta.icon;
  const createdAt = new Date(n.created_at).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={cn(
        "bg-surface-1 border rounded-xl p-4 flex gap-3 transition-colors",
        !n.is_read
          ? "border-brand-accent/25 bg-brand-accent/5"
          : "border-border-subtle"
      )}
    >
      {/* Icon badge */}
      <div
        className={cn(
          "w-8 h-8 rounded-lg shrink-0 flex items-center justify-center",
          variantBg[meta.variant]
        )}
      >
        <Icon size={15} className={variantIcon[meta.variant]} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={cn(
            "text-sm font-medium",
            n.is_read ? "text-text-secondary" : "text-text-primary"
          )}>
            {n.subject}
          </p>
          <span className="text-xs text-text-tertiary whitespace-nowrap shrink-0">{createdAt}</span>
        </div>
        <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">{n.body}</p>
      </div>

      {!n.is_read && (
        <button
          onClick={onMarkRead}
          disabled={markingRead}
          className="text-text-tertiary hover:text-text-primary transition-colors shrink-0 disabled:opacity-50 self-start mt-0.5"
          title="Marcar como lida"
        >
          <Check size={14} />
        </button>
      )}
    </div>
  );
}
