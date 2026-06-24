import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Chaves de API",
};

export default function ApiKeysLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
