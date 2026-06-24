"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
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
import { notificationService } from "@/lib/services";
import { useAuthStore } from "@/store/auth";

const BELL_ICON_MAP: Record<string, LucideIcon> = {
  "payment.processed":          CheckCircle2,
  "payment.failed":             XCircle,
  "payment.due_soon":           AlertTriangle,
  "payment.dunning_d3":         XCircle,
  "subscription.created":       CheckCircle2,
  "subscription.renewed":       RefreshCw,
  "subscription.suspended":     AlertTriangle,
  "subscription.expired":       XCircle,
  "subscription.expiring_soon": AlertTriangle,
  "subscription.grace_period":  AlertTriangle,
  "subscription.plan_changed":  Info,
  "subscription.cancelled":     XCircle,
  "service.provisioned":        Server,
  "customer.suspended":         UserX,
  "customer.reactivated":       UserCheck,
  "invitation.created":         Mail,
  "invitation.accepted":        UserCheck,
};

export default function NotificationBell() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { me } = useAuthStore();

  const { data } = useQuery({
    queryKey: ["notifications-bell"],
    queryFn: () => notificationService.list(),
    refetchInterval: 30_000,
    enabled: !!me?.customer,
  });

  const markAllMutation = useMutation({
    mutationFn: notificationService.markAllRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications-bell"] }),
  });

  const markOneMutation = useMutation({
    mutationFn: notificationService.markRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications-bell"] }),
  });

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const unread = data?.unread_count ?? 0;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="Notificações"
        className="relative p-2 text-text-tertiary hover:text-text-primary hover:bg-surface-2 rounded-lg transition-colors"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.75}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-0.5 text-[10px] font-bold bg-brand-accent text-slate-950 rounded-full flex items-center justify-center leading-none">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-11 w-80 bg-surface-1 border border-border-subtle rounded-xl shadow-lg z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle">
            <span className="text-sm font-semibold text-text-primary">Notificações</span>
            {unread > 0 && (
              <button
                onClick={() => markAllMutation.mutate()}
                disabled={markAllMutation.isPending}
                className="text-xs text-text-tertiary hover:text-text-primary disabled:opacity-50"
              >
                Marcar todas como lidas
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-border-subtle">
            {!data?.results.length ? (
              <p className="px-4 py-6 text-sm text-center text-text-tertiary">Nenhuma notificação</p>
            ) : (
              data.results.map((n) => {
                const Icon = BELL_ICON_MAP[n.event_type] ?? Info;
                return (
                  <button
                    key={n.id}
                    onClick={() => !n.is_read && markOneMutation.mutate(n.id)}
                    className={`w-full text-left px-4 py-3 hover:bg-surface-2 transition-colors flex items-start gap-3 ${
                      n.is_read ? "" : "bg-info-muted"
                    }`}
                  >
                    <Icon
                      size={14}
                      className={`mt-0.5 shrink-0 ${n.is_read ? "text-text-tertiary" : "text-info"}`}
                    />
                    <div className="min-w-0">
                      <p
                        className={`text-sm font-medium truncate ${
                          n.is_read ? "text-text-secondary" : "text-text-primary"
                        }`}
                      >
                        {n.subject}
                      </p>
                      <p className="text-xs text-text-tertiary mt-0.5 line-clamp-2">{n.body}</p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
          <div className="px-4 py-2.5 border-t border-border-subtle">
            <Link
              href="/dashboard/notifications"
              onClick={() => setOpen(false)}
              className="text-xs text-text-secondary hover:text-text-primary underline"
            >
              Ver todas as notificações →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
