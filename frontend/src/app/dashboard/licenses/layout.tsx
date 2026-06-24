import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Licenças",
};

export default function LicensesLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
