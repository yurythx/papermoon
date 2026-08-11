import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Integração SSO",
};

export default function KeycloakIntegrationLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
