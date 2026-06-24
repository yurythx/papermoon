import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Auditoria",
};

export default function AuditLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
