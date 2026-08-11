import { CopyButton } from "@/components/compound/copy-button";
import { cn } from "@/lib/utils";

interface CodeBlockProps {
  code: string;
  className?: string;
}

/**
 * Bloco de código multi-linha com botão de copiar no canto. Sem syntax
 * highlighting de propósito — nenhuma lib disso está instalada no projeto
 * (nem prism/shiki/highlight.js), e adicionar uma só pra isto seria escopo
 * demais pra uma página. Monoespaçado simples, consistente com o resto do
 * dashboard (ver o <code> inline de api-keys/page.tsx).
 */
export function CodeBlock({ code, className }: CodeBlockProps) {
  return (
    <div
      className={cn(
        "relative bg-surface-3 border border-border-subtle rounded-lg overflow-hidden",
        className
      )}
    >
      <div className="absolute top-2 right-2">
        <CopyButton value={code} label="Copiar" className="bg-surface-2 px-2 py-1 rounded border border-border-subtle" />
      </div>
      <pre className="overflow-x-auto p-4 pt-3">
        <code className="whitespace-pre font-mono text-xs text-text-primary leading-relaxed">{code}</code>
      </pre>
    </div>
  );
}
