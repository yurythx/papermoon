import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Detalhes da Licença",
};

export default function LicenseDetailLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
