import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  /** Quando informado, mostra "{count} <label>" à esquerda (align="between"). */
  count?: number;
  countLabel?: (count: number) => string;
  align?: "between" | "center";
  className?: string;
}

// Extraído de 5 páginas que reimplementavam o mesmo par de botões
// Anterior/Próxima + "página / total" à mão — qualquer ajuste de UX
// (paginação por teclado, tamanho de página, etc.) só precisa mudar aqui.
export function Pagination({
  page,
  totalPages,
  onPageChange,
  count,
  countLabel,
  align = "between",
  className,
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const nav = (
    <div className="flex items-center gap-2">
      <Button
        variant="secondary"
        size="sm"
        disabled={page === 1}
        onClick={() => onPageChange(Math.max(1, page - 1))}
      >
        Anterior
      </Button>
      <span className="px-3 text-text-tertiary text-sm">
        {page} / {totalPages}
      </span>
      <Button
        variant="secondary"
        size="sm"
        disabled={page === totalPages}
        onClick={() => onPageChange(Math.min(totalPages, page + 1))}
      >
        Próxima
      </Button>
    </div>
  );

  if (align === "center" || count === undefined) {
    return <div className={cn("flex items-center justify-center", className)}>{nav}</div>;
  }

  return (
    <div className={cn("flex items-center justify-between text-sm text-text-secondary", className)}>
      <span>{countLabel ? countLabel(count) : count}</span>
      {nav}
    </div>
  );
}
