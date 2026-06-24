const CUSTOMERS = [
  { name: "Clínica Saúde+", sector: "Saúde" },
  { name: "Grupo Logística BR", sector: "Logística" },
  { name: "Metalúrgica Forta", sector: "Indústria" },
  { name: "Escola Digital", sector: "Educação" },
  { name: "Imobiliária Prime", sector: "Imóveis" },
  { name: "DataCenter Norte", sector: "TI" },
  { name: "Farmácia Vida", sector: "Farmácia" },
  { name: "ConstrutoraBR", sector: "Construção" },
  { name: "Hotel Bella Vista", sector: "Hotelaria" },
  { name: "Agência Criativa", sector: "Marketing" },
  { name: "Distribuidora Apex", sector: "Atacado" },
  { name: "Clínica OrthoMax", sector: "Saúde" },
  { name: "Varejo Expresso", sector: "Varejo" },
  { name: "Oficina TechAuto", sector: "Automotivo" },
];

function CustomerBadge({ name, sector }: { name: string; sector: string }) {
  return (
    <div className="flex items-center gap-3 px-5 py-3 rounded-xl bg-surface-1 border border-border-subtle shrink-0 select-none">
      <div className="w-7 h-7 rounded-lg bg-brand-accent/15 flex items-center justify-center shrink-0">
        <span className="text-[11px] font-black text-brand-accent">
          {name[0]}
        </span>
      </div>
      <div>
        <p className="text-xs font-semibold text-text-primary whitespace-nowrap">{name}</p>
        <p className="text-[10px] text-text-tertiary whitespace-nowrap">{sector}</p>
      </div>
    </div>
  );
}

export function LogosMarquee() {
  const doubled = [...CUSTOMERS, ...CUSTOMERS];

  return (
    <section className="py-16 border-y border-border-subtle overflow-hidden">
      <div className="max-w-6xl mx-auto px-6 mb-8 text-center">
        <p className="text-xs font-semibold text-text-tertiary uppercase tracking-widest">
          Empresas que já usam a PaperMoon
        </p>
      </div>
      <div
        className="flex gap-4 animate-marquee"
        style={{ width: "max-content" }}
        aria-hidden="true"
      >
        {doubled.map((c, i) => (
          <CustomerBadge key={i} name={c.name} sector={c.sector} />
        ))}
      </div>
    </section>
  );
}
