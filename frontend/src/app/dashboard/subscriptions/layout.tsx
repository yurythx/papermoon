import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Assinaturas",
};

export default function SubscriptionsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
