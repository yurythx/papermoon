import type { Metadata } from "next";
import { BackofficeShell } from "@/components/layout/backoffice-shell";

export const metadata: Metadata = {
  title: {
    template: "%s | Backoffice — PaperMoon",
    default: "Backoffice",
  },
};

export default function BackofficeLayout({ children }: { children: React.ReactNode }) {
  return <BackofficeShell>{children}</BackofficeShell>;
}
