import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Aguardando configuração",
  description: "Sua empresa está sendo provisionada. Em breve você terá acesso completo.",
};

export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
