import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export type CardTone = "neutral" | "success" | "warning" | "danger" | "info";

// Contraste de fundo em vez de contorno — ver plano de redesign "estilo AWS"
// (cards da AWS não usam borda pesada, só bg-surface-1 contra o bg-surface-0
// da página). `neutral` cobre o card genérico; os demais tons reaproveitam as
// mesmas classes `-muted` já usadas em badges/alertas pra manter consistência
// visual entre "card de status" e "chip de status".
const toneClasses: Record<CardTone, string> = {
  neutral: "bg-surface-1",
  success: "bg-success-muted",
  warning: "bg-warning-muted",
  danger: "bg-danger-muted",
  info: "bg-info-muted",
};

interface CardStyleProps {
  tone?: CardTone;
  /** Liga hover de elevação sutil (fundo mais claro + leve translate + shadow) —
   * usar em cards clicáveis/navegáveis, não em painéis estáticos. */
  interactive?: boolean;
  className?: string;
}

/**
 * Classe utilitária de card, exportada separadamente do componente `Card` pra
 * poder ser aplicada direto num `<Link>` do Next (navegação client-side exige
 * que o Link seja o elemento raiz, não algo embrulhado num <div>).
 */
export function cardClass({ tone = "neutral", interactive = false, className }: CardStyleProps = {}): string {
  return cn(
    "rounded-2xl p-5",
    toneClasses[tone],
    interactive && "transition-all duration-200 hover:bg-surface-2 hover:-translate-y-0.5 hover:shadow-lg",
    className
  );
}

interface CardProps extends CardStyleProps, React.HTMLAttributes<HTMLDivElement> {}

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { tone, interactive, className, ...props },
  ref
) {
  return <div ref={ref} className={cardClass({ tone, interactive, className })} {...props} />;
});
