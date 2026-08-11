import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Providers } from "./providers";

// Hospedadas localmente (src/fonts/) em vez de next/font/google — o build de
// produção roda numa rede sem rota IPv6 estável, e fonts.googleapis.com/
// fonts.gstatic.com têm registro AAAA: o fetch do next/font/google trava
// tentando IPv6 até estourar timeout, derrubando o build inteiro de forma
// intermitente. Arquivos .woff2 são o subset "latin" da fonte variável
// (mesmo arquivo que o Google serviria pra subsets: ["latin"]), baixados uma
// vez — nunca precisa de rede no build a partir de agora.
const geist = localFont({
  src: "../fonts/Inter-Variable.woff2",
  variable: "--font-geist",
  display: "swap",
  weight: "100 900",
});

const geistMono = localFont({
  src: "../fonts/JetBrainsMono-Variable.woff2",
  variable: "--font-geist-mono",
  display: "swap",
  weight: "100 800",
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
