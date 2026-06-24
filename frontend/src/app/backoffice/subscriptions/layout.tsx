import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Assinaturas",
};

export default function BackofficeSubscriptionsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
