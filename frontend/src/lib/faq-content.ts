export interface FaqItem {
  q: string;
  a: string;
}

export const LANDING_FAQS: FaqItem[] = [
  {
    q: "O que a PaperMoon faz exatamente?",
    a: "A PaperMoon instala, configura e mantém ferramentas open-source na infraestrutura da sua empresa — da comunicação ao monitoramento, do helpdesk à virtualização. Além disso, somos especialistas em redes corporativas, cabeamento estruturado, manutenção de servidores e políticas de backup. Cuidamos de toda a pilha de TI para que você foque no negócio.",
  },
  {
    q: "O servidor (VPS) é meu ou de vocês?",
    a: "É seu. Para implantações de software (n8n, Chatwoot, Tailscale, GLPI, Zabbix etc.), você contrata e paga a VPS diretamente ao provedor de sua escolha (Hostinger, Hetzner, AWS...). A PaperMoon acessa via SSH para instalar e configurar — os dados e o acesso root ficam sempre com você. Para hardware físico (servidores bare-metal, TrueNAS, Proxmox em máquina própria), o equipamento é 100% seu.",
  },
  {
    q: "Como funciona o processo de implantação?",
    a: "Após a contratação, fazemos um levantamento técnico da sua operação (usuários, serviços, volumes). Então você provisiona o servidor e nos passa o acesso — nossa equipe cuida de toda a instalação, configuração e integração. Ao final, realizamos o treinamento da equipe e entregamos a documentação completa. Para serviços físicos (redes, cabeamento), fazemos a visita presencial.",
  },
  {
    q: "Qual a diferença entre os serviços mensais e de implantação única?",
    a: "Serviços de implantação única (como n8n, GLPI, Zabbix, Proxmox, TrueNAS, Nextcloud, AAPanel) são configurações pontuais: você paga uma vez pela instalação e treinamento. Ajustes futuros ou expansões são cobrados sob demanda. Assinaturas e planos de suporte contínuo (quando disponíveis para o serviço) incluem manutenção, atualizações e monitoramento, onde você paga um valor mensal para garantir a estabilidade e evolução do ambiente.",
  },
  {
    q: "Vocês fazem serviço presencial para redes e cabeamento?",
    a: "Sim. Redes corporativas, cabeamento estruturado (Cat5e/Cat6/fibra) e manutenção de servidores físicos são serviços presenciais — um técnico da PaperMoon vai até o local. Para implantações de Proxmox em bare-metal, a instalação inicial também é presencial. Entre em contato informando sua localização para verificarmos a cobertura.",
  },
  {
    q: "Como funciona o suporte após a implantação?",
    a: "Serviços de assinatura contínua incluem suporte via WhatsApp e e-mail em dias úteis — atualizações, ajustes de configuração e monitoramento de disponibilidade fazem parte do plano. Para projetos de implantação única, oferecemos suporte técnico por 30 dias após a entrega; após esse período, o suporte adicional pode ser contratado sob demanda.",
  },
  {
    q: "Posso contratar mais de um serviço ao mesmo tempo?",
    a: "Sim, e é comum. Por exemplo: n8n + Chatwoot para automação de atendimento, Proxmox + TrueNAS para virtualização com storage centralizado, ou cabeamento estruturado + infraestrutura de rede antes de instalar qualquer software. Consultamos cada caso para propor a ordem de implantação que faz mais sentido para a operação.",
  },
];
