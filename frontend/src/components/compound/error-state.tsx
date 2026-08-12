import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}

// Distinct from EmptyState on purpose: "sem dados" and "a requisição falhou"
// are different situations and must never render the same message — showing
// EmptyState on a fetch error tells the user something false (e.g. "nenhuma
// fatura encontrada" when their invoices just failed to load).
export function ErrorState({
  title = "Não foi possível carregar os dados",
  description = "Verifique sua conexão e tente novamente.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div className={cn("flex flex-col items-center py-16 text-center", className)}>
      <div className="bg-danger/10 rounded-full p-5 mb-4 border border-danger/20">
        <AlertTriangle size={28} className="text-danger" />
      </div>
      <h3 className="text-base font-semibold text-text-primary mb-2">{title}</h3>
      <p className="text-sm text-text-secondary max-w-xs mb-6">{description}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Tentar novamente
        </Button>
      )}
    </div>
  );
}
