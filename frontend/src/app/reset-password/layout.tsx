import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Nova senha",
  description: "Defina uma nova senha para sua conta PaperMoon.",
};

export default function ResetPasswordLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
