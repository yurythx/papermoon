"use client";

import { useId, useRef, useState } from "react";
import Link from "next/link";
import { Check, Users } from "lucide-react";

interface Plan {
  id: string;
  label: string;
  name: string;
  subtitle: string;
  userHighlight: string;
  price: string;
  period: string;
  priceNote: string;
  items: string[];
  cta: string;
  ctaHref: string;
  highlight: boolean;
}

const PLANS: Plan[] = [
  {
    id: "starter",
    label: "Starter",
    name: "Starter",
    subtitle: "Ideal para pequenas equipes começando com WhatsApp oficial.",
    userHighlight: "Até 2 agentes simultâneos",
    price: "R$ 299",
    period: "/mês",
    priceNote: "R$ 2.988/ano (economize 2 meses)",
    items: [
      "1 número WhatsApp oficial",
      "2 agentes no Chatwoot",
      "5.000 mensagens/mês",
      "n8n com até 5 fluxos ativos",
      "Templates HSM básicos",
      "Suporte via e-mail (D+1)",
    ],
    cta: "Começar com Starter",
    ctaHref: "/register",
    highlight: false,
  },
  {
    id: "pro",
    label: "Pro",
    name: "Profissional",
    subtitle: "Para times em crescimento que precisam de automação avançada.",
    userHighlight: "Até 8 agentes simultâneos",
    price: "R$ 499",
    period: "/mês",
    priceNote: "R$ 4.788/ano (economize 2 meses)",
    items: [
      "1 número WhatsApp oficial",
      "8 agentes no Chatwoot",
      "25.000 mensagens/mês",
      "n8n ilimitado (fluxos sem limite)",
      "Templates HSM inclusos",
      "Chatbot visual com IA",
      "Suporte prioritário (4h úteis)",
    ],
    cta: "Começar com Pro",
    ctaHref: "/register",
    highlight: true,
  },
  {
    id: "enterprise",
    label: "Enterprise",
    name: "Enterprise",
    subtitle: "Para operações de grande volume com SLA e suporte dedicado.",
    userHighlight: "Agentes ilimitados",
    price: "R$ 999",
    period: "/mês",
    priceNote: "Plano personalizado disponível sob consulta",
    items: [
      "Múltiplos números WhatsApp",
      "Agentes ilimitados",
      "Mensagens ilimitadas",
      "n8n dedicado por empresa",
      "Onboarding assistido (4h)",
      "SLA 2h · Suporte premium 24/5",
      "Gerente de conta dedicado",
    ],
    cta: "Falar com vendas",
    ctaHref: "mailto:contato@papermoon.com.br",
    highlight: false,
  },
];

export function PricingTabs() {
  const [activeId, setActiveId] = useState<string>("pro");
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const tabListId = useId();
  const plan = PLANS.find((p) => p.id === activeId) ?? PLANS[1];

  function selectTab(index: number) {
    const normalizedIndex = (index + PLANS.length) % PLANS.length;
    const targetPlan = PLANS[normalizedIndex];
    setActiveId(targetPlan.id);
    tabRefs.current[normalizedIndex]?.focus();
  }

  return (
    <div>
      {/* Tab pills */}
      <div
        role="tablist"
        aria-label="Planos PaperMoon"
        className="flex gap-1 bg-surface-2 p-1 rounded-xl max-w-xs mx-auto mb-10 border border-border-subtle"
      >
        {PLANS.map((p, index) => (
          <button
            key={p.id}
            id={`${tabListId}-tab-${p.id}`}
            role="tab"
            type="button"
            aria-selected={activeId === p.id}
            aria-controls={`${tabListId}-panel-${p.id}`}
            tabIndex={activeId === p.id ? 0 : -1}
            onClick={() => setActiveId(p.id)}
            onKeyDown={(event) => {
              if (event.key === "ArrowRight" || event.key === "ArrowDown") {
                event.preventDefault();
                selectTab(index + 1);
              } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
                event.preventDefault();
                selectTab(index - 1);
              } else if (event.key === "Home") {
                event.preventDefault();
                selectTab(0);
              } else if (event.key === "End") {
                event.preventDefault();
                selectTab(PLANS.length - 1);
              }
            }}
            ref={(element) => {
              tabRefs.current[index] = element;
            }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all duration-150 ${
              activeId === p.id
                ? "bg-surface-0 text-text-primary shadow-sm"
                : "text-text-tertiary hover:text-text-secondary"
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Plan card */}
      <div
        role="tabpanel"
        id={`${tabListId}-panel-${plan.id}`}
        aria-labelledby={`${tabListId}-tab-${plan.id}`}
        tabIndex={0}
        className={`max-w-md mx-auto rounded-2xl border p-8 transition-all duration-200 ${
          plan.highlight
            ? "bg-gradient-to-b from-surface-2 to-surface-1 border-brand-accent/40 shadow-xl shadow-glow-accent"
            : "bg-surface-1 border-border-subtle"
        }`}
      >
        {plan.highlight && (
          <div className="flex justify-center mb-6">
            <span className="px-4 py-1 rounded-full bg-brand-accent text-[rgb(var(--papermoon-midnight-fixed-rgb))] text-[10px] font-bold uppercase tracking-wider">
              Mais popular
            </span>
          </div>
        )}

        <div className="mb-6">
          <h3 className="text-xl font-bold text-text-primary">{plan.name}</h3>
          <p className="text-sm text-text-secondary mt-1">{plan.subtitle}</p>
        </div>

        {/* User highlight */}
        <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-surface-3 border border-border-subtle mb-6">
          <Users size={15} className="text-brand-accent shrink-0" />
          <span className="text-sm font-semibold text-text-primary">{plan.userHighlight}</span>
        </div>

        {/* Features */}
        <ul className="space-y-3 mb-8">
          {plan.items.map((item) => (
            <li key={item} className="flex items-start gap-2.5 text-sm text-text-secondary">
              <div
                className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                  plan.highlight ? "bg-brand-accent/20" : "bg-surface-3"
                }`}
              >
                <Check size={10} className={plan.highlight ? "text-brand-accent" : "text-text-tertiary"} />
              </div>
              {item}
            </li>
          ))}
        </ul>

        {/* Price */}
        <div className="mb-6 pb-6 border-b border-border-subtle">
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-black text-text-primary">{plan.price}</span>
            <span className="text-sm text-text-tertiary">{plan.period}</span>
          </div>
          <p className="text-xs text-text-tertiary mt-1.5">{plan.priceNote}</p>
        </div>

        <Link
          href={plan.ctaHref}
          className={`block text-center py-3.5 rounded-xl font-semibold text-sm transition-all ${
            plan.highlight
              ? "bg-brand-accent text-[rgb(var(--papermoon-midnight-fixed-rgb))] hover:bg-brand-accent/90 shadow-lg shadow-glow-accent"
              : "bg-surface-3 border border-border-default text-text-primary hover:border-border-focus hover:bg-surface-4"
          } focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-1`}
        >
          {plan.cta}
        </Link>
      </div>
    </div>
  );
}
