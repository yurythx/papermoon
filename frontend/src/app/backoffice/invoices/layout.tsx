import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Faturas",
};

export default function BackofficeInvoicesLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
