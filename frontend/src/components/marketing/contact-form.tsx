"use client";

import { useState } from "react";
import { Send, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

const SERVICES = [
  "Tailscale — VPN / Mesh Network",
  "n8n — Automação de Processos",
  "Chatwoot — Atendimento Multicanal",
  "GLPI — Helpdesk / ITSM",
  "Zabbix — Monitoramento",
  "Proxmox VE — Virtualização",
  "TrueNAS — NAS / Storage",
  "Nextcloud — Nuvem privada",
  "AAPanel — Hospedagem web",
  "Redes e cabeamento estruturado",
  "Manutenção de servidores / computadores",
  "Outro / Dúvida geral",
];

type Status = "idle" | "loading" | "success" | "error";

export function ContactForm() {
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [form, setForm] = useState({
    name: "", email: "", phone: "", service: "", message: "",
  });

  function set(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (status === "loading") return;
    setStatus("loading");
    setErrorMsg("");

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (res.ok) {
        setStatus("success");
        setForm({ name: "", email: "", phone: "", service: "", message: "" });
      } else {
        const data = await res.json().catch(() => ({}));
        const msg =
          data?.error?.message ??
          data?.detail ??
          (res.status === 429 ? "Muitas tentativas. Aguarde antes de enviar novamente." : "Erro ao enviar. Tente novamente.");
        setErrorMsg(msg);
        setStatus("error");
      }
    } catch {
      setErrorMsg("Erro de conexão. Verifique sua internet e tente novamente.");
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-12 text-center">
        <div className="w-14 h-14 rounded-full bg-success-muted border border-success/25 flex items-center justify-center">
          <CheckCircle2 size={28} className="text-success" />
        </div>
        <div>
          <p className="text-base font-semibold text-text-primary">Mensagem enviada!</p>
          <p className="text-sm text-text-secondary mt-1">
            Nossa equipe responde em até 1 dia útil.
          </p>
        </div>
        <button
          onClick={() => setStatus("idle")}
          className="text-xs text-text-tertiary hover:text-text-secondary underline underline-offset-4 transition-colors"
        >
          Enviar outra mensagem
        </button>
      </div>
    );
  }

  const inputClass =
    "w-full px-4 py-2.5 rounded-xl bg-surface-2 border border-border-subtle text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-brand-accent/50 focus:ring-1 focus:ring-brand-accent/20 transition-colors";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">
            Nome <span className="text-brand-accent">*</span>
          </label>
          <input
            type="text"
            required
            value={form.name}
            onChange={set("name")}
            placeholder="Seu nome"
            className={inputClass}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">
            E-mail <span className="text-brand-accent">*</span>
          </label>
          <input
            type="email"
            required
            value={form.email}
            onChange={set("email")}
            placeholder="seu@email.com"
            className={inputClass}
          />
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">
            WhatsApp / Telefone
          </label>
          <input
            type="tel"
            value={form.phone}
            onChange={set("phone")}
            placeholder="(11) 99999-9999"
            className={inputClass}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">
            Serviço de interesse
          </label>
          <select value={form.service} onChange={set("service")} className={inputClass}>
            <option value="">Selecione...</option>
            {SERVICES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1.5">
          Mensagem <span className="text-brand-accent">*</span>
        </label>
        <textarea
          required
          rows={4}
          value={form.message}
          onChange={set("message")}
          placeholder="Conte brevemente sobre sua operação e o que precisa..."
          className={`${inputClass} resize-none`}
        />
      </div>

      {status === "error" && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-brand-accent/10 border border-brand-accent/20 text-xs text-brand-accent">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          {errorMsg}
        </div>
      )}

      <button
        type="submit"
        disabled={status === "loading"}
        className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-brand-accent text-[rgb(var(--papermoon-midnight-fixed-rgb))] text-sm font-semibold hover:bg-brand-accent/90 active:scale-[0.98] transition-all disabled:opacity-60 disabled:cursor-not-allowed shadow-lg shadow-glow-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-border-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface-1"
      >
        {status === "loading" ? (
          <><Loader2 size={15} className="animate-spin" /> Enviando...</>
        ) : (
          <><Send size={15} /> Enviar mensagem</>
        )}
      </button>
    </form>
  );
}
