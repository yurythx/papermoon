import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const geist = Inter({
  subsets: ["latin"],
  variable: "--font-geist",
  display: "swap",
});

const geistMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    template: "%s | PaperMoon",
    default: "PaperMoon | Plataforma SaaS multi-tenant para operacoes e servicos digitais",
  },
  description:
    "PaperMoon e uma plataforma SaaS multi-tenant para operacoes, atendimento, automacao e gestao de servicos digitais com backend como fonte unica de verdade.",
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
  },
  openGraph: {
    type: "website",
    siteName: "PaperMoon",
    locale: "pt_BR",
    title: "PaperMoon | Plataforma SaaS multi-tenant para operacoes e servicos digitais",
    description:
      "Multi-tenancy, observabilidade, integracoes e operacao centralizada em uma plataforma preparada para crescimento enterprise.",
  },
  twitter: {
    card: "summary_large_image",
    title: "PaperMoon | Plataforma SaaS multi-tenant para operacoes e servicos digitais",
    description:
      "Plataforma orientada a dominio para operacoes, automacao, suporte e servicos digitais.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={`${geist.variable} ${geistMono.variable} font-sans`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
