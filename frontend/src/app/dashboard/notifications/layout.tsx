import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Notificações",
};

export default function NotificationsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
