import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Check, AlertTriangle, Shield, Server, CreditCard, Wrench } from "lucide-react";
import { LandingNav } from "@/components/marketing/nav";

export const metadata: Metadata = {
  title: "Termos de Uso — PaperMoon",
  description: "Termos de uso e responsabilidades da plataforma PaperMoon. Leia antes de contratar.",
};

const LAST_UPDATED = "10 de junho de 2026";

export default function TermosPage() {
  return (
    <div className="min-h-screen bg-surface-0 text-text-primary">
      <LandingNav />

      <div className="max-w-3xl mx-auto px-6 pt-28 pb-24">
        {/* Header */}
        <div className="mb-10">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-text-tertiary hover:text-text-secondary transition-colors mb-6"
          >
            <ArrowLeft size={12} />
            Voltar ao início
          </Link>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight mb-3">Termos de Uso</h1>
          <p className="text-sm text-text-tertiary">Última atualização: {LAST_UPDATED}</p>
          <p className="text-sm text-text-secondary mt-4 leading-relaxed">
            Ao contratar os serviços da PaperMoon, você concorda com os termos abaixo. Leia com atenção
            — este documento define claramente o que é responsabilidade da PaperMoon e o que é
            responsabilidade do cliente.
          </p>
        </div>

        <div className="space-y-10">

          {/* 1. Modelo de prestação de serviço */}
          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand-accent/10 flex items-center justify-center shrink-0">
                <Wrench size={14} className="text-brand-accent" />
              </div>
              <h2 className="text-base font-bold text-text-primary">1. Modelo de prestação de serviço</h2>
            </div>
            <div className="prose-sm text-text-secondary leading-relaxed space-y-4 pl-11">
              <p>
                A PaperMoon oferece dois modelos de contratação, conforme o serviço escolhido:
              </p>

              <div className="space-y-3">
                <div className="rounded-lg border border-border-subtle bg-surface-1 p-4 space-y-2">
                  <p className="text-xs font-semibold text-text-primary">Serviços mensais — software gerenciado</p>
                  <p className="text-xs leading-relaxed">
                    Inclui os serviços <strong className="text-text-primary">WhatsApp via API Meta</strong> e{" "}
                    <strong className="text-text-primary">WhatsApp via Evolution API</strong> (com Chatwoot e n8n).
                    O cliente paga mensalmente e recebe instalação, manutenção contínua, atualizações e suporte.
                    Os softwares são instalados na VPS do próprio cliente — a PaperMoon não hospeda dados.
                  </p>
                </div>
                <div className="rounded-lg border border-border-subtle bg-surface-1 p-4 space-y-2">
                  <p className="text-xs font-semibold text-text-primary">Serviços de implantação — cobrança única</p>
                  <p className="text-xs leading-relaxed">
                    Inclui <strong className="text-text-primary">GLPI, Zabbix, Proxmox, TrueNAS, Nextcloud e AAPanel</strong>,
                    além de <strong className="text-text-primary">redes, cabeamento estruturado e manutenção de servidores físicos</strong>.
                    São projetos pontuais: levantamento técnico, execução, treinamento e documentação — pagos uma única vez.
                    Ajustes e expansões posteriores são contratados separadamente.
                  </p>
                </div>
              </div>

              <p>Em ambos os modelos, a PaperMoon cobre:</p>
              <ul className="space-y-1.5">
                {[
                  "Levantamento técnico e planejamento da implantação",
                  "Instalação e configuração dos softwares ou infraestrutura física contratados",
                  "Treinamento da equipe do cliente ao final da implantação",
                  "Documentação técnica do ambiente entregue",
                  "Suporte técnico via e-mail e WhatsApp em dias úteis (9h–18h)",
                  "Atualizações de versão (somente nos planos mensais)",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-xs">
                    <Check size={11} className="text-brand-accent shrink-0 mt-0.5" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* 2. Responsabilidades do cliente */}
          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-warning-muted flex items-center justify-center shrink-0">
                <Server size={14} className="text-warning" />
              </div>
              <h2 className="text-base font-bold text-text-primary">2. Responsabilidades do cliente</h2>
            </div>
            <div className="rounded-xl border border-warning/20 bg-warning-muted p-5 space-y-3 ml-11">
              <p className="text-xs text-text-secondary leading-relaxed">
                Os itens abaixo são de <strong className="text-text-primary">responsabilidade exclusiva do cliente</strong>.
                A PaperMoon não se responsabiliza por falhas, cobranças ou perdas decorrentes do não cumprimento destes itens.
              </p>
              <ul className="space-y-2.5">
                {[
                  {
                    title: "Informações técnicas precisas antes da implantação",
                    detail: "O cliente deve fornecer mapeamento do ambiente (número de usuários, equipamentos, layout da rede ou planta do local para cabeamento) antes do início do projeto. Alterações de escopo após o início podem gerar custo adicional.",
                  },
                  {
                    title: "Contratação e pagamento do servidor (VPS)",
                    detail: "Para serviços baseados em software, o cliente deve contratar e manter ativa uma VPS com especificações mínimas (2 vCPUs, 4 GB RAM, 40 GB SSD). O pagamento é feito diretamente ao provedor de hospedagem — não à PaperMoon.",
                  },
                  {
                    title: "Acesso remoto ao servidor",
                    detail: "O cliente deve fornecer acesso root via SSH para que a PaperMoon realize instalações, atualizações e manutenção. A revogação do acesso sem aviso prévio suspende automaticamente o suporte técnico.",
                  },
                  {
                    title: "Acesso físico ao local (serviços presenciais)",
                    detail: "Para redes, cabeamento estruturado, instalação de servidores físicos e manutenção presencial, o cliente deve garantir acesso ao local na data agendada. O não comparecimento na data combinada pode gerar cobrança de visita técnica.",
                  },
                  {
                    title: "Backup e preservação de dados",
                    detail: "O cliente é responsável por manter backups dos dados armazenados no servidor antes de qualquer intervenção técnica. Para serviços de implantação (cobrança única), a PaperMoon realiza o backup do ambiente existente antes de iniciar — mas a política de backup contínua é responsabilidade do cliente.",
                  },
                  {
                    title: "Registro do número no Meta Business Manager (somente API Meta)",
                    detail: "O número WhatsApp deve ser registrado na conta Meta Business Manager do próprio cliente. A PaperMoon auxilia no processo, mas a titularidade do número é sempre do cliente. Um cartão de crédito válido deve estar cadastrado na conta Meta para cobrir os custos de conversas cobrados pela Meta.",
                  },
                  {
                    title: "Conformidade com políticas de fornecedores externos",
                    detail: "Para serviços que dependem de plataformas de terceiros (Meta, Evolution API), o uso deve estar em conformidade com as políticas de uso de cada plataforma. Violações são de responsabilidade do cliente e podem resultar em suspensão do serviço pelo próprio fornecedor.",
                  },
                ].map((item) => (
                  <li key={item.title} className="space-y-0.5">
                    <div className="flex items-start gap-2">
                      <AlertTriangle size={11} className="text-warning shrink-0 mt-0.5" />
                      <span className="text-xs font-semibold text-text-primary">{item.title}</span>
                    </div>
                    <p className="text-xs text-text-secondary leading-relaxed pl-5">{item.detail}</p>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          {/* 3. Privacidade e dados */}
          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-service-whatsapp/10 flex items-center justify-center shrink-0">
                <Shield size={14} className="text-service-whatsapp" />
              </div>
              <h2 className="text-base font-bold text-text-primary">3. Privacidade e dados</h2>
            </div>
            <div className="space-y-3 pl-11 text-xs text-text-secondary leading-relaxed">
              <p>
                Como os softwares são instalados no servidor do próprio cliente, os dados das
                conversas, contatos e históricos ficam armazenados <strong className="text-text-primary">exclusivamente na VPS do cliente</strong>.
                A PaperMoon não tem acesso contínuo aos dados de conversas — o acesso SSH é utilizado
                apenas para manutenção técnica.
              </p>
              <p>
                Para fins de suporte, a PaperMoon pode solicitar logs de erro ao cliente. Esses logs
                são usados exclusivamente para diagnóstico e nunca compartilhados com terceiros.
              </p>
            </div>
          </section>

          {/* 4. Pagamento e cancelamento */}
          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-surface-2 flex items-center justify-center shrink-0">
                <CreditCard size={14} className="text-text-secondary" />
              </div>
              <h2 className="text-base font-bold text-text-primary">4. Pagamento e cancelamento</h2>
            </div>
            <div className="space-y-3 pl-11 text-xs text-text-secondary leading-relaxed">
              <p>
                <strong className="text-text-primary">Serviços mensais</strong> são cobrados via boleto ou cartão de crédito a cada 30 dias.
                O não pagamento por mais de 15 dias corridos suspende o suporte técnico e as atualizações,
                mas <strong className="text-text-primary">não remove os softwares do servidor do cliente</strong> —
                os dados e a operação não são afetados imediatamente.
              </p>
              <p>
                <strong className="text-text-primary">Serviços de implantação</strong> (cobrança única) são faturados em até 2 parcelas:
                50% no aceite do projeto e 50% na entrega. Não há reembolso após o início da execução.
              </p>
              <p>
                O cancelamento de planos mensais pode ser solicitado a qualquer momento via e-mail para{" "}
                <a href="mailto:contato@papermoon.com.br" className="text-brand-accent hover:underline">
                  contato@papermoon.com.br
                </a>
                {" "}com 30 dias de antecedência. Não há multa por cancelamento após os primeiros 3 meses.
                Após o cancelamento, os softwares permanecem instalados no servidor do cliente — a PaperMoon não realiza remoção remota.
              </p>
            </div>
          </section>

          {/* 5. Limitação de responsabilidade */}
          <section className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-surface-2 flex items-center justify-center shrink-0">
                <AlertTriangle size={14} className="text-text-secondary" />
              </div>
              <h2 className="text-base font-bold text-text-primary">5. Limitação de responsabilidade</h2>
            </div>
            <div className="space-y-3 pl-11 text-xs text-text-secondary leading-relaxed">
              <p>
                A PaperMoon não se responsabiliza por:
              </p>
              <ul className="space-y-1.5">
                {[
                  "Indisponibilidade causada por falha no servidor do cliente, no provedor de hospedagem ou no fornecimento de energia no local",
                  "Perda de dados por ausência de backup por parte do cliente antes de uma intervenção",
                  "Danos em equipamentos físicos causados por surtos elétricos, uso inadequado ou desgaste natural",
                  "Cobranças de fornecedores externos (Meta, Evolution API, provedores de VPS) decorrentes do uso dos serviços",
                  "Suspensão ou ban de contas em plataformas de terceiros (Meta Business, número WhatsApp) por violação de políticas dessas plataformas",
                  "Falhas em integrações com sistemas de terceiros (CRM, ERP, planilhas) configuradas ou alteradas pelo próprio cliente",
                  "Atrasos causados por obras, acesso restrito ao local ou mudanças de escopo solicitadas após o início do projeto",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2 text-xs">
                    <span className="text-text-tertiary shrink-0">·</span>
                    {item}
                  </li>
                ))}
              </ul>
              <p>
                A responsabilidade máxima da PaperMoon em qualquer hipótese limita-se ao valor total pago pelo cliente no mês de ocorrência do evento (para planos mensais) ou ao valor da parcela vigente (para projetos de implantação).
              </p>
            </div>
          </section>

          {/* 6. Disposições gerais */}
          <section className="space-y-4">
            <h2 className="text-base font-bold text-text-primary pl-11">6. Disposições gerais</h2>
            <div className="space-y-3 pl-11 text-xs text-text-secondary leading-relaxed">
              <p>
                Estes termos são regidos pela legislação brasileira. Eventuais disputas serão
                resolvidas no foro da comarca de domicílio da PaperMoon.
              </p>
              <p>
                A PaperMoon pode atualizar estes termos a qualquer momento. O cliente será notificado
                com 15 dias de antecedência por e-mail. O uso continuado dos serviços após essa
                data implica aceitação dos novos termos.
              </p>
              <p>
                Dúvidas sobre estes termos? Entre em contato:{" "}
                <a href="mailto:contato@papermoon.com.br" className="text-brand-accent hover:underline">
                  contato@papermoon.com.br
                </a>
              </p>
            </div>
          </section>

        </div>

        {/* Footer nav */}
        <div className="mt-16 pt-8 border-t border-border-subtle flex flex-col sm:flex-row items-center justify-between gap-4">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-text-tertiary hover:text-text-secondary transition-colors"
          >
            <ArrowLeft size={13} />
            Voltar ao início
          </Link>
          <p className="text-xs text-text-tertiary">
            © {new Date().getFullYear()} PaperMoon. Todos os direitos reservados.
          </p>
        </div>
      </div>
    </div>
  );
}
