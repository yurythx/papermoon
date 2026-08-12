import Link from "next/link";
import { PaperMoonMark } from "@/components/common/papermoon-mark";

const NAV_LINKS = [
  { label: "Serviços", href: "/servicos" },
  { label: "Blog", href: "/blog" },
  { label: "Sobre", href: "/sobre" },
  { label: "Termos", href: "/termos" },
];

const SERVICE_LINKS = [
  { label: "WhatsApp API Meta", href: "/servicos/whatsapp-api" },
  { label: "WhatsApp Evolution API", href: "/servicos/whatsapp-evolution" },
  { label: "GLPI", href: "/servicos/glpi" },
  { label: "Zabbix", href: "/servicos/zabbix" },
  { label: "Proxmox VE", href: "/servicos/proxmox" },
  { label: "TrueNAS", href: "/servicos/truenas" },
  { label: "Nextcloud", href: "/servicos/nextcloud" },
  { label: "AAPanel", href: "/servicos/aapanel" },
];

interface FooterProps {
  /** "minimal" (padrão) = uma linha, usado na maioria das páginas públicas.
   * "full" = 4 colunas + barra inferior, reservado pra home. */
  variant?: "full" | "minimal";
  /** <PaperMoonMark> usa <defs id> internos pro gradiente do SVG — precisa de
   * sufixo único por página renderizada pra não colidir se houver mais de uma
   * instância na mesma árvore (ex: nav + footer). */
  idSuffix: string;
}

export function Footer({ variant = "minimal", idSuffix }: FooterProps) {
  const year = new Date().getFullYear();

  if (variant === "minimal") {
    return (
      <footer className="border-t border-border-subtle py-8">
        <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2">
            <PaperMoonMark idSuffix={`footer-${idSuffix}`} />
            <span className="text-sm font-bold text-text-primary">PaperMoon</span>
          </Link>
          <p className="text-xs text-text-tertiary">© {year} PaperMoon. Todos os direitos reservados.</p>
          <div className="flex gap-4">
            {NAV_LINKS.map((l) => (
              <Link key={l.href} href={l.href} className="text-xs text-text-secondary hover:text-text-primary transition-colors">
                {l.label}
              </Link>
            ))}
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className="border-t border-border-subtle bg-surface-1/50 py-12">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10 mb-10">
          <div className="space-y-3 lg:col-span-1">
            <div className="flex items-center gap-2.5">
              <PaperMoonMark idSuffix={`footer-${idSuffix}`} size={24} />
              <span className="font-bold text-text-primary">PaperMoon</span>
            </div>
            <p className="text-xs text-text-tertiary leading-relaxed">
              Instalação e manutenção de ferramentas open-source na sua VPS: helpdesk, monitoramento, virtualização e comunicação.
            </p>
          </div>

          <div>
            <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Navegação</p>
            <ul className="space-y-2">
              {NAV_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Serviços</p>
            <ul className="space-y-2">
              {SERVICE_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-3">Acesso</p>
            <ul className="space-y-2">
              <li>
                <Link href="/login" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                  Entrar no painel
                </Link>
              </li>
              <li>
                <Link href="/register" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                  Criar conta
                </Link>
              </li>
              <li>
                <Link href="/forgot-password" className="text-sm text-text-tertiary hover:text-text-secondary transition-colors">
                  Recuperar senha
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-border-subtle flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-text-tertiary">© {year} PaperMoon. Todos os direitos reservados.</p>
          <div className="flex gap-4 text-xs text-text-tertiary">
            <Link href="/termos" className="hover:text-text-secondary transition-colors">
              Termos de uso
            </Link>
            <span>Privacidade</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
