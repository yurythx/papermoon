import {
  MessageSquare,
  Filter,
  Shield,
  Wrench,
  Eye,
  Server,
  HardDrive,
  Cloud,
  LayoutDashboard,
  MessageCircle,
  Network,
  Layers,
  Cpu,
  Archive,
  Monitor,
  Users,
  FolderOpen,
  Globe,
  KeyRound,
  Building2,
  FileText,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

export interface ServiceStep {
  num: string;
  title: string;
  description: string;
}

export interface ServiceFeatureGroup {
  title: string;
  items: string[];
}

export interface ServiceScreenshot {
  src: string;
  alt: string;
  caption: string;
}

export interface ServiceFAQ {
  q: string;
  a: string;
}

export interface ServiceContent {
  slug: string;
  name: string;
  tagline: string;
  description: string;
  about: string;
  differentials: string[];
  comingSoon: boolean;
  icon: LucideIcon;
  color: string;
  colorBg: string;
  colorBorder: string;
  colorText: string;
  heroImage: string | null;
  heroImageAlt: string;
  metaTitle: string;
  metaDescription: string;
  papermoonDoes: string[];
  clientDoes: string[];
  steps: ServiceStep[];
  featureGroups: ServiceFeatureGroup[];
  screenshots: ServiceScreenshot[];
  faqs: ServiceFAQ[];
  prerequisites: string[];
}

const SERVICE_TONES = {
  whatsapp: {
    color: "text-service-whatsapp",
    colorBg: "bg-service-whatsapp/10",
    colorBorder: "border-service-whatsapp/25",
    colorText: "text-service-whatsapp",
  },
  accent: {
    color: "text-brand-accent",
    colorBg: "bg-brand-accent/10",
    colorBorder: "border-brand-accent/25",
    colorText: "text-brand-accent",
  },
  info: {
    color: "text-info",
    colorBg: "bg-info-muted",
    colorBorder: "border-info/25",
    colorText: "text-info",
  },
  warning: {
    color: "text-warning",
    colorBg: "bg-warning-muted",
    colorBorder: "border-warning/25",
    colorText: "text-warning",
  },
  success: {
    color: "text-success",
    colorBg: "bg-success-muted",
    colorBorder: "border-success/25",
    colorText: "text-success",
  },
  neutral: {
    color: "text-text-secondary",
    colorBg: "bg-surface-2",
    colorBorder: "border-border-subtle",
    colorText: "text-text-secondary",
  },
} as const;

export const SERVICES: ServiceContent[] = [
  /* ── WhatsApp Business API ─────────────────────────────────────── */
  {
    slug: "whatsapp-api",
    name: "WhatsApp Business API",
    tagline: "Atendimento profissional no número oficial da sua empresa.",
    description:
      "Conecte o número da empresa à API oficial da Meta. Zero risco de ban, múltiplos agentes, templates aprovados e total controle da sua conta.",
    about:
      "A WhatsApp Business API foi lançada pela Meta em 2018 para atender empresas que precisavam de escala no atendimento via WhatsApp sem depender do aplicativo convencional — que suporta apenas um dispositivo por vez. Antes dela, muitas empresas recorriam a soluções não-oficiais baseadas em automação do WhatsApp Web, tecnicamente proibidas pelos termos de uso e sujeitas a ban permanente.\n\nCom a API oficial, o número da empresa é verificado diretamente pela Meta, recebe o selo verde de empresa verificada e passa a ter acesso à infraestrutura de mensageria de nível enterprise: entrega garantida por SLA, sem limite de conversas simultâneas, suporte a templates aprovados (HSM) para campanhas ativas e integração nativa com ferramentas de atendimento como o Chatwoot.\n\nA PaperMoon conduz todo o processo: desde a criação e verificação da conta no Meta Business Manager até a configuração do webhook entre a API Meta e o Chatwoot instalado na sua VPS. Nossa equipe conhece os requisitos de aprovação da Meta e reduz significativamente o tempo e os erros no processo de onboarding.",
    differentials: [
      "Número verificado diretamente pela Meta — sem risco de ban",
      "A PaperMoon guia todo o processo de aprovação no Meta Business Manager, passo a passo",
      "Integração imediata com Chatwoot: equipe atende assim que o número é aprovado",
      "Monitoramento contínuo da conectividade entre a API Meta e a VPS do cliente",
      "Suporte na aprovação dos primeiros templates HSM — maior taxa de sucesso na primeira tentativa",
    ],
    comingSoon: false,
    icon: Shield,
    ...SERVICE_TONES.whatsapp,
    heroImage: null,
    heroImageAlt: "WhatsApp Business API — painel Meta Business Manager",
    metaTitle: "WhatsApp Business API Oficial — PaperMoon",
    metaDescription:
      "Conecte seu número à API oficial da Meta com a PaperMoon. Número verificado, sem risco de ban, múltiplos agentes e templates aprovados.",
    papermoonDoes: [
      "Guia o processo de registro do número no Meta Business Manager",
      "Conecta a API Meta ao Chatwoot instalado na sua VPS",
      "Configura o webhook de recebimento de mensagens",
      "Auxilia na aprovação dos primeiros templates HSM",
      "Monitora a conectividade do número com a API Meta",
    ],
    clientDoes: [
      "Criar e manter a conta no Meta Business Manager",
      "Registrar o número WABA (WhatsApp Business Account)",
      "Cadastrar cartão de crédito válido na conta Meta",
      "Arcar com os custos de conversas e disparos cobrados pela Meta",
      "Obter opt-in dos destinatários antes de enviar mensagens ativas",
      "Manter conformidade com as políticas de uso da Meta",
    ],
    steps: [
      {
        num: "01",
        title: "Crie sua conta Meta Business",
        description:
          "Acesse business.whatsapp.com e registre sua empresa. Você precisará de um CNPJ e um número de telefone dedicado ao WhatsApp corporativo. A PaperMoon guia todo o processo.",
      },
      {
        num: "02",
        title: "Verificação e aprovação pela Meta",
        description:
          "A Meta verifica sua empresa e aprova o número. A duração dessa etapa varia conforme a documentação e a análise da conta. Após aprovado, seu número aparece como verificado para todos os contatos.",
      },
      {
        num: "03",
        title: "Conectamos ao Chatwoot na sua VPS",
        description:
          "Com o número aprovado, a PaperMoon configura o webhook entre a API Meta e o Chatwoot instalado na sua VPS. Em minutos sua equipe já recebe e responde mensagens no painel.",
      },
    ],
    featureGroups: [
      {
        title: "Confiabilidade",
        items: [
          "Número verificado diretamente pela Meta",
          "Zero risco de ban — API oficial, não app clone",
          "SLA de entrega de mensagens garantido pela Meta",
          "Uptime de 99,9% na infraestrutura de mensagens Meta",
        ],
      },
      {
        title: "Capacidade",
        items: [
          "Múltiplos agentes no mesmo número simultaneamente",
          "Sem limite de conversas simultâneas",
          "1.000 conversas de serviço gratuitas por mês",
          "Volume escalonável sem troca de número ou plano",
        ],
      },
      {
        title: "Mensagens ativas",
        items: [
          "Templates HSM aprovados pela Meta para disparos",
          "Categorias: Marketing, Utility, Authentication",
          "Envio de mídia: imagens, documentos, vídeos, localização",
          "Botões interativos e listas de opções",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença entre API oficial e apps não-oficiais?",
        a: "Apps não-oficiais (como versões modificadas) simulam o WhatsApp e violam os termos de uso — o número pode ser banido permanentemente sem aviso. A API oficial é a única forma autorizada pela Meta para uso empresarial. Com ela, seu número é verificado, protegido e escalável.",
      },
      {
        q: "Preciso de cartão cadastrado na Meta?",
        a: "Sim. Um cartão de crédito ou débito válido deve estar na conta Meta Business Manager para ativar o número e enviar mensagens ativas. As conversas iniciadas pela empresa (notificações, campanhas) são cobradas pela Meta direto no cartão — não pela PaperMoon.",
      },
      {
        q: "Posso usar meu número atual?",
        a: "Sim, desde que ele não esteja em uso no WhatsApp pessoal ou no WhatsApp Business app. O número precisa ser migrado para a API, o que requer desinstalar o app atual. A PaperMoon orienta todo o processo de portabilidade.",
      },
      {
        q: "Quanto tempo leva para o número ser aprovado?",
        a: "A aprovação depende da análise da Meta e da consistência da documentação enviada. A PaperMoon acompanha esse processo, orienta os ajustes necessários e só agenda a integração final quando a conta estiver liberada para operação.",
      },
      {
        q: "Posso fazer disparos em massa com a API oficial da Meta?",
        a: "A API oficial da Meta permite enviar templates de mensagem (HSM) para listas de contatos — notificações, cobranças, confirmações. O volume é limitado pelos níveis de qualidade do número e pelo plano de mensagens da Meta. A PaperMoon configura a integração com o n8n para automação dos disparos e orienta sobre os limites e boas práticas para manter o número com alta reputação.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 2 vCPU, 4 GB RAM, 40 GB SSD)",
      "Conta Meta Business Manager criada e verificada com CNPJ",
      "Número de telefone dedicado não vinculado ao WhatsApp pessoal ou Business app",
      "Domínio próprio com acesso ao painel DNS para apontar subdomínio",
      "Acesso SSH à VPS com usuário root ou sudo",
      "Cartão de crédito/débito cadastrado na conta Meta para cobranças de mensagens",
    ],
  },

  /* ── Chatwoot ──────────────────────────────────────────────────── */
  {
    slug: "chatwoot",
    name: "Chatwoot",
    tagline: "Toda a sua equipe no mesmo número, com histórico completo.",
    description:
      "Inbox multiagente open-source instalado na sua VPS. Atribua conversas, crie etiquetas, meça SLA e gerencie toda a operação de atendimento em um único painel.",
    about:
      "O Chatwoot surgiu em 2019 como um projeto open-source criado por Pranav Raj S e equipe, com o objetivo de oferecer uma alternativa gratuita e auto-hospedada a ferramentas como Intercom e Zendesk — que cobram por agente e mantêm os dados do cliente em servidores de terceiros. Hoje conta com mais de 20 mil estrelas no GitHub e é adotado por empresas de todos os portes ao redor do mundo.\n\nA proposta central do Chatwoot é unificar todos os canais de atendimento — WhatsApp, e-mail, Instagram, Telegram — em um único painel, com histórico completo por contato, atribuição de conversas entre agentes, criação de etiquetas e métricas de SLA em tempo real. Diferente de SaaS pagos, o Chatwoot instalado na sua VPS significa que seus dados de atendimento ficam inteiramente sob controle da sua empresa.\n\nA PaperMoon realiza a instalação completa do Chatwoot com banco de dados PostgreSQL, Redis, Nginx com SSL e todas as configurações de produção. Configuramos as inboxes por canal, criamos os perfis de agente e conectamos ao WhatsApp Business API e ao n8n — entregando o ambiente pronto para sua equipe operar com segurança e contexto completo.",
    differentials: [
      "Open-source e auto-hospedado: seus dados de atendimento nunca saem da sua VPS",
      "Instalação production-ready com PostgreSQL, Redis, Nginx e SSL — sem etapas manuais",
      "Integração imediata com WhatsApp Business API Meta e n8n configurada pela PaperMoon",
      "Atualizações de versão gerenciadas pela nossa equipe — sem downtime ou perda de dados",
      "Custo zero de licença por agente — escale a equipe sem aumentar a fatura de software",
    ],
    comingSoon: false,
    icon: MessageSquare,
    ...SERVICE_TONES.info,
    heroImage: "https://www.chatwoot.com/images/dashboard-dark.webp",
    heroImageAlt: "Chatwoot — painel de atendimento multiagente com WhatsApp",
    metaTitle: "Chatwoot — Inbox multiagente instalado na sua VPS — PaperMoon",
    metaDescription:
      "A PaperMoon instala e configura o Chatwoot na sua VPS. Múltiplos agentes, histórico completo, etiquetas, SLA e métricas de atendimento.",
    papermoonDoes: [
      "Instala e configura o Chatwoot na sua VPS",
      "Integra com a API Meta e o n8n",
      "Cria as caixas de entrada (inboxes) por canal",
      "Configura agentes, equipes e permissões iniciais",
      "Mantém o Chatwoot atualizado para novas versões",
      "Monitora a disponibilidade do serviço",
    ],
    clientDoes: [
      "Contratar e manter a VPS onde o Chatwoot é instalado",
      "Gerenciar agentes, permissões e equipes no dia a dia",
      "Exportar ou fazer backup dos históricos de conversa",
      "Configurar horários de atendimento e respostas padrão",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação na sua VPS",
        description:
          "A PaperMoon instala o Chatwoot na VPS que você contratar (Hostinger, HostGator, AWS...). Todo o setup de banco de dados, Redis e configurações de produção é feito por nós.",
      },
      {
        num: "02",
        title: "Configuração da caixa de entrada",
        description:
          "Conectamos a inbox do Chatwoot ao seu número WhatsApp via API Meta. Criamos os perfis dos agentes, equipes e definimos as regras de atribuição conforme sua operação.",
      },
      {
        num: "03",
        title: "Sua equipe começa a atender",
        description:
          "Cada agente acessa com login próprio. Conversas chegam distribuídas, com histórico completo do contato, etiquetas e notas internas. Métricas de SLA disponíveis em tempo real.",
      },
    ],
    featureGroups: [
      {
        title: "Gestão de conversas",
        items: [
          "Múltiplos agentes no mesmo número WhatsApp",
          "Atribuição manual ou automática de conversas",
          "Transferência entre agentes e equipes",
          "Notas internas visíveis só para a equipe",
          "Respostas rápidas (canned responses) configuráveis",
          "Histórico completo por contato",
        ],
      },
      {
        title: "Organização",
        items: [
          "Etiquetas personalizáveis por conversa ou contato",
          "Filtros avançados: por agente, status, canal, etiqueta",
          "Inbox unificado para WhatsApp, e-mail e outros canais",
          "Busca em todo o histórico de mensagens",
        ],
      },
      {
        title: "Métricas e SLA",
        items: [
          "Dashboard de métricas por agente e equipe",
          "Tempo médio de resposta e de resolução",
          "Relatório de conversas por período",
          "Alertas de SLA configuráveis por urgência",
        ],
      },
    ],
    screenshots: [
      {
        src: "https://www.chatwoot.com/images/dashboard-dark.webp",
        alt: "Painel principal do Chatwoot com conversas WhatsApp",
        caption: "Painel principal — todas as conversas em um só lugar",
      },
    ],
    faqs: [
      {
        q: "O Chatwoot é open-source. Por que pagar a PaperMoon?",
        a: "O Chatwoot é gratuito para instalar, mas exige infraestrutura (VPS, banco PostgreSQL, Redis, S3 para arquivos), configuração técnica e manutenção contínua (atualizações, backups, monitoramento). A PaperMoon cuida de tudo isso para que sua equipe foque no atendimento, não na infraestrutura.",
      },
      {
        q: "Quantos agentes posso ter?",
        a: "Não há limite de agentes — o Chatwoot é instalado na sua VPS, então o limite real é a capacidade do servidor. Para a maioria das operações, um VPS básico (2 vCPUs, 4 GB RAM) suporta confortavelmente 20 a 50 agentes simultâneos.",
      },
      {
        q: "Posso ter múltiplos canais além do WhatsApp?",
        a: "Sim. O Chatwoot suporta e-mail, Instagram, Telegram, Facebook Messenger e API própria. A PaperMoon configura os canais que você precisar na mesma instalação.",
      },
      {
        q: "Os dados ficam onde?",
        a: "Todos os históricos de conversa ficam armazenados exclusivamente na sua VPS — você tem controle total. A PaperMoon não armazena dados de conversas em nenhum servidor próprio.",
      },
      {
        q: "É possível configurar chatbot ou respostas automáticas no Chatwoot?",
        a: "Sim. O Chatwoot suporta respostas rápidas (canned responses) para agilizar o atendimento, e integra nativamente com o n8n para automações mais avançadas — bot de FAQ, coleta de dados e roteamento automático de conversas. A PaperMoon configura a integração entre Chatwoot e n8n como parte da entrega.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 2 vCPU, 4 GB RAM, 40 GB SSD)",
      "Domínio próprio com acesso ao painel DNS para apontar subdomínio",
      "Acesso SSH à VPS com usuário root ou sudo",
      "SMTP configurado ou conta de e-mail para envio de notificações (opcional)",
    ],
  },

  /* ── n8n ───────────────────────────────────────────────────────── */
  {
    slug: "n8n",
    name: "n8n",
    tagline: "Filtre, automatize e conecte antes de chegar ao agente.",
    description:
      "Plataforma de automação open-source instalada na sua VPS. Cada cliente tem seus próprios fluxos: qualificação, bot de FAQ, roteamento por departamento e integrações com CRM e ERP.",
    about:
      "O n8n foi criado em 2019 pelo alemão Jan Oberhauser como alternativa self-hosted ao Zapier — com uma diferença crucial: os fluxos e os dados ficam inteiramente no servidor do cliente, não em infraestrutura da plataforma. Em pouco tempo chegou a mais de 40 mil estrelas no GitHub e hoje conta com mais de 400 integrações nativas com ferramentas de negócios, desenvolvimento e operações.\n\nSua arquitetura de nós visuais — onde cada bloco representa uma etapa de automação — permite criar desde simples notificações automáticas até pipelines complexos com lógica condicional, loops e transformação de dados, sem necessidade de programação. Empresas de atendimento o utilizam principalmente como camada de triagem entre o WhatsApp e os agentes humanos: o n8n responde as dúvidas mais comuns automaticamente, coleta dados do cliente e encaminha para o agente certo com o contexto já preenchido.\n\nA PaperMoon instala o n8n na VPS do cliente já integrado ao Chatwoot e ao webhook da Meta, e configura os fluxos iniciais conforme o processo de atendimento da empresa: bot de FAQ, mensagem automática fora do horário, roteamento por departamento e coleta de dados cadastrais. Documentamos cada fluxo para que sua equipe possa ajustá-los com autonomia.",
    differentials: [
      "Auto-hospedado: seus fluxos de automação e dados de clientes ficam na sua VPS",
      "Mais de 400 integrações nativas — conecta qualquer sistema com API sem código",
      "A PaperMoon entrega os fluxos iniciais prontos e documentados, não apenas a instalação",
      "Zero dependência de plano SaaS: não paga por operação nem por usuário",
      "Integração nativa com Chatwoot e WhatsApp API já configurada na entrega",
    ],
    comingSoon: false,
    icon: Filter,
    ...SERVICE_TONES.warning,
    heroImage:
      "https://n8niostorageaccount.blob.core.windows.net/n8nio-strapi-blobs-stage/assets/teams_of_agents_9a90248bb1.png",
    heroImageAlt: "n8n — editor de workflows de automação de atendimento",
    metaTitle: "n8n — Automação de atendimento instalada na sua VPS — PaperMoon",
    metaDescription:
      "A PaperMoon instala e configura o n8n na sua VPS. Fluxos de qualificação, bot de FAQ, roteamento e integrações com CRM, planilhas e ERP.",
    papermoonDoes: [
      "Instala e configura o n8n na sua VPS",
      "Cria os fluxos iniciais de qualificação e roteamento",
      "Integra o n8n com o Chatwoot e a API Meta",
      "Configura o bot de perguntas frequentes (FAQ)",
      "Mantém o n8n atualizado e monitorado",
      "Ajuda na criação de novos fluxos conforme a operação cresce",
    ],
    clientDoes: [
      "Contratar e manter a VPS onde o n8n é instalado",
      "Fornecer credenciais de APIs externas a integrar (CRM, ERP, etc.)",
      "Aprovar e validar os fluxos criados",
      "Solicitar ajustes nos fluxos via suporte",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação e integração",
        description:
          "A PaperMoon instala o n8n na sua VPS e conecta ao webhook do WhatsApp. Toda mensagem que chegar passará pelos seus fluxos antes de aparecer para um agente.",
      },
      {
        num: "02",
        title: "Configuração dos fluxos",
        description:
          "Mapeamos sua operação: horários de atendimento, departamentos, perguntas frequentes e regras de roteamento. Criamos os primeiros fluxos no editor visual do n8n.",
      },
      {
        num: "03",
        title: "Filtro em produção",
        description:
          "Mensagens chegam, passam pelo n8n — que triaga, responde automaticamente ou encaminha — e só então chegam ao agente certo no Chatwoot, já qualificadas e organizadas.",
      },
    ],
    featureGroups: [
      {
        title: "Qualificação automática",
        items: [
          "Bot de perguntas frequentes (FAQ) 24 horas por dia",
          "Coleta de nome, CPF, número do pedido ou qualquer dado",
          "Mensagem automática fora do horário de atendimento",
          "Confirmação automática de recebimento da mensagem",
        ],
      },
      {
        title: "Roteamento inteligente",
        items: [
          "Roteamento por palavra-chave ou intenção",
          "Atribuição automática ao departamento correto",
          "Roteamento por horário (comercial, pós-horário, feriado)",
          "Encaminhamento por agente disponível ou especialista",
        ],
      },
      {
        title: "Integrações",
        items: [
          "Conexão com planilhas Google Sheets ou Excel",
          "Consulta de dados em CRM (HubSpot, Pipedrive, RD Station...)",
          "Integração com sistemas ERP via API REST ou webhook",
          "Notificações automáticas para Slack, e-mail ou Teams",
          "Abertura automática de chamados no GLPI",
        ],
      },
    ],
    screenshots: [
      {
        src: "https://n8niostorageaccount.blob.core.windows.net/n8nio-strapi-blobs-stage/assets/teams_of_agents_9a90248bb1.png",
        alt: "n8n — editor de fluxos de automação",
        caption: "Editor visual do n8n — crie fluxos sem escrever código",
      },
    ],
    faqs: [
      {
        q: "Preciso saber programar para usar o n8n?",
        a: "Não. O n8n tem um editor visual onde você cria fluxos arrastando e conectando blocos. A PaperMoon cria os fluxos iniciais para você e treina sua equipe para ajustes simples. Para automações mais complexas, nossa equipe cuida do desenvolvimento.",
      },
      {
        q: "O n8n substitui um agente humano?",
        a: "Não completamente, mas reduz drasticamente o volume de perguntas repetitivas. O n8n resolve as dúvidas mais comuns automaticamente (horário, endereço, status de pedido) e encaminha para agentes apenas o que realmente precisa de atenção humana.",
      },
      {
        q: "Consigo integrar com meu sistema atual?",
        a: "Muito provavelmente sim. O n8n possui mais de 400 integrações nativas (HubSpot, Salesforce, Google Sheets, Slack, Trello, RD Station...) e suporta qualquer sistema com API REST ou webhook. Consulte nossa equipe para avaliar seu caso específico.",
      },
      {
        q: "E se o n8n ficar fora do ar?",
        a: "A PaperMoon monitora a disponibilidade do n8n na sua VPS. Em caso de queda, as mensagens do WhatsApp continuam chegando no Chatwoot — apenas sem passar pelos fluxos automáticos. Nossa equipe é notificada automaticamente e age para restaurar o serviço.",
      },
      {
        q: "O n8n salva os dados das automações no meu servidor?",
        a: "Sim. Com o n8n self-hosted, todos os dados de execução dos fluxos — logs, payloads de entrada e saída, histórico de erros — ficam armazenados no banco de dados da sua VPS. Nenhuma informação dos seus clientes ou fluxos passa pelos servidores da n8n GmbH.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 1 vCPU, 2 GB RAM, 20 GB SSD)",
      "Domínio próprio com acesso ao painel DNS para apontar subdomínio",
      "Acesso SSH à VPS com usuário root ou sudo",
    ],
  },

  /* ── GLPI ──────────────────────────────────────────────────────── */
  {
    slug: "glpi",
    name: "GLPI",
    tagline: "Central de helpdesk e gestão de chamados de TI instalada na sua VPS.",
    description:
      "Sistema open-source de gestão de chamados de TI instalado na sua VPS. Parametrização completa de categorias, SLAs, filas de atendimento e base de conhecimento — entregue pronto para uso.",
    about:
      "O GLPI (Gestionnaire Libre de Parc Informatique) é desenvolvido desde 2003 pelo projeto francês INDEPNET e hoje mantido pela empresa Teclib'. Com mais de 330 mil instalações registradas em todo o mundo, é o sistema de helpdesk open-source mais utilizado em ambientes corporativos de TI no Brasil — com adoção forte em órgãos públicos, universidades e empresas de médio porte.\n\nSua proposta vai além do simples registro de chamados: o GLPI integra helpdesk, inventário de ativos (computadores, licenças, contratos), base de conhecimento, gestão de mudanças e relatórios de SLA em uma única plataforma. O módulo de inventário pode ser alimentado automaticamente via agente FusionInventory ou OCS Inventory, eliminando planilhas de controle manuais.\n\nA PaperMoon entrega o GLPI instalado, configurado e pronto para uso — não apenas a instalação técnica, mas a parametrização completa do processo de TI do cliente: criamos as categorias de chamado, definimos os SLAs por urgência e impacto, configuramos as filas de atendimento por equipe, ativamos as notificações automáticas por e-mail e realizamos o treinamento dos técnicos. Cobrança única, sem mensalidade.",
    differentials: [
      "Entrega com parametrização completa: SLAs, categorias e filas configuradas conforme seu processo real",
      "Inventário de TI integrado — nenhuma planilha separada para controlar equipamentos",
      "Treinamento da equipe técnica incluído no escopo de entrega",
      "Cobrança única, sem mensalidade — pagou uma vez, é seu para sempre",
      "Open-source maduro com 20+ anos de desenvolvimento e comunidade ativa",
    ],
    comingSoon: false,
    icon: Wrench,
    ...SERVICE_TONES.info,
    heroImage: null,
    heroImageAlt: "GLPI — sistema de helpdesk e chamados de TI",
    metaTitle: "GLPI — Helpdesk instalado na sua VPS — PaperMoon",
    metaDescription:
      "A PaperMoon instala e parametriza o GLPI na sua VPS: categorias, SLA, filas de atendimento, base de conhecimento e treinamento da equipe. Implantação única, sem mensalidade.",
    papermoonDoes: [
      "Instala e configura o GLPI na sua VPS",
      "Parametriza categorias, SLAs e filas de atendimento conforme seu negócio",
      "Importa base de usuários e equipamentos",
      "Configura notificações automáticas por e-mail",
      "Documenta toda a configuração e realiza treinamento da equipe de TI",
    ],
    clientDoes: [
      "Contratar e manter a VPS onde o GLPI é instalado",
      "Gerenciar técnicos, categorias e SLAs no dia a dia",
      "Gerenciar usuários e permissões após o treinamento",
      "Fazer backup dos dados e histórico de chamados",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação na VPS",
        description:
          "A PaperMoon instala o GLPI com banco MariaDB na sua VPS e configura o ambiente de produção com SSL e backups automáticos.",
      },
      {
        num: "02",
        title: "Parametrização e SLA",
        description:
          "Mapeamos sua operação de TI e configuramos categorias de chamados, SLAs por urgência, filas de atendimento, perfis de técnicos e regras de escalonamento — tudo alinhado ao seu processo.",
      },
      {
        num: "03",
        title: "Equipe de TI em produção",
        description:
          "Técnicos recebem chamados organizados por categoria e SLA, com histórico completo de cada solicitação. Treinamos toda a equipe para operar o sistema com autonomia e clareza sobre o processo.",
      },
    ],
    featureGroups: [
      {
        title: "Gestão de chamados",
        items: [
          "Abertura de tickets via e-mail ou portal web",
          "Categorização por tipo de solicitação e urgência",
          "SLA configurável por categoria com alertas de prazo",
          "Notificações automáticas por e-mail a cada atualização",
          "Histórico completo de todas as interações",
        ],
      },
      {
        title: "Inventário de TI",
        items: [
          "Controle de equipamentos, licenças e contratos",
          "Vinculação de chamados a ativos do inventário",
          "Relatórios de uso e manutenção por ativo",
          "Importação via OCS Inventory ou agente próprio",
        ],
      },
      {
        title: "Base de conhecimento",
        items: [
          "Artigos de solução para problemas recorrentes",
          "Busca integrada ao abrir chamados",
          "Histórico de resoluções para referência da equipe",
          "Redução do tempo de resposta com soluções documentadas",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "A cobrança é mensal ou única?",
        a: "A implantação do GLPI é cobrada como projeto único — sem mensalidade. Você paga uma vez pela instalação, parametrização, configuração de SLAs e treinamento. Suporte técnico posterior (ajustes, atualizações, novos usuários) é contratado sob demanda, via invoice avulsa.",
      },
      {
        q: "Posso integrar o GLPI com outros sistemas depois?",
        a: "Sim. O GLPI possui API REST e suporta integrações com diversas ferramentas. Integrações adicionais — como abertura de chamados via outros canais ou conexão com sistemas de monitoramento — podem ser contratadas separadamente como projetos complementares.",
      },
      {
        q: "Posso contratar GLPI e Zabbix juntos?",
        a: "Sim. O GLPI e o Zabbix podem ser implantados em conjunto na mesma VPS ou em VPSs separadas, conforme a preferência da sua equipe. A contratação conjunta é comum em equipes de TI que querem helpdesk e monitoramento na mesma plataforma.",
      },
      {
        q: "Qual a diferença entre o GLPI e outras ferramentas como Freshdesk ou Jira Service?",
        a: "Freshdesk e Jira Service são SaaS pagos por agente — cada novo técnico aumenta a mensalidade indefinidamente. O GLPI é open-source instalado na sua VPS: sem limite de agentes, sem mensalidade, com dados inteiramente sob controle da empresa. Para equipes de TI que precisam de ITIL, inventário de ativos e base de conhecimento sem custo recorrente, o GLPI é a escolha natural.",
      },
      {
        q: "É possível fazer inventário automático de equipamentos com o GLPI?",
        a: "Sim. O GLPI integra com o FusionInventory ou o agente GLPI Agent, que coletam automaticamente o inventário de hardware e software das estações — processador, memória, disco, aplicativos instalados, número de série. O resultado alimenta o módulo de ativos do GLPI, eliminando planilhas manuais de controle de inventário.",
      },
    ],
    prerequisites: [
      "VPS ou servidor com Ubuntu 22.04 LTS (mínimo 2 vCPU, 4 GB RAM, 40 GB SSD)",
      "Domínio próprio com acesso ao painel DNS para apontar subdomínio",
      "Acesso SSH à VPS com usuário root ou sudo",
      "Lista de categorias de chamados, SLAs e grupos de atendimento desejados",
    ],
  },

  /* ── Zabbix ────────────────────────────────────────────────────── */
  {
    slug: "zabbix",
    name: "Zabbix",
    tagline: "Monitoramento de infraestrutura instalado na sua VPS.",
    description:
      "Plataforma open-source de monitoramento instalada na sua VPS. Dashboards em tempo real, triggers configuráveis e alertas por e-mail quando servidores, serviços ou métricas saem do padrão esperado.",
    about:
      "O Zabbix foi criado por Alexei Vladishev em 2001 como projeto interno de monitoramento e liberado como open-source em 2004. Hoje é desenvolvido e mantido pela empresa letã Zabbix LLC e é considerado a plataforma de monitoramento de infraestrutura open-source mais robusta e madura do mercado, com adoção em grandes empresas e operadoras de telecomunicações ao redor do mundo.\n\nO Zabbix monitora tudo: servidores físicos e virtuais, switches e roteadores, containers Docker, aplicações web, bancos de dados, arquivos de log e muito mais — via agente instalado no host, SNMP, ICMP ou checks HTTP. Quando uma métrica ultrapassa um limite definido (trigger), o sistema envia alertas imediatos por e-mail, Telegram, Slack ou SMS, com escalonamento automático conforme o nível de severidade.\n\nA PaperMoon instala o Zabbix na VPS do cliente, descobre automaticamente todos os hosts da rede, configura os templates de monitoramento para os serviços em produção (Nginx, PostgreSQL, Docker, etc.) e ajusta os thresholds ideais para o ambiente específico. Criamos dashboards customizados por servidor e serviço, e configuramos as notificações para chegarem ao canal certo da equipe de TI.",
    differentials: [
      "Auto-descoberta de hosts na rede: inventário de infraestrutura atualizado automaticamente",
      "Templates prontos para todos os serviços comuns: Nginx, PostgreSQL, Docker, Linux, VMware",
      "Alertas com escalonamento: notifica técnico júnior, sênior e gestor conforme o tempo sem resolução",
      "Dashboards customizados por servidor, serviço ou cliente — não apenas a visão padrão",
      "Histórico de performance para análise de tendências e planejamento de capacidade",
    ],
    comingSoon: false,
    icon: Eye,
    ...SERVICE_TONES.accent,
    heroImage: null,
    heroImageAlt: "Zabbix — monitoramento de infraestrutura e alertas",
    metaTitle: "Zabbix — Monitoramento instalado na sua VPS — PaperMoon",
    metaDescription:
      "A PaperMoon instala o Zabbix na sua VPS: agentes nos servidores, triggers configuráveis, dashboards e alertas por e-mail. Monitore em tempo real. Implantação única, sem mensalidade.",
    papermoonDoes: [
      "Instala e configura o Zabbix na sua VPS",
      "Configura os agentes Zabbix nos servidores monitorados",
      "Cria dashboards e triggers para os itens críticos",
      "Configura alertas por e-mail com escalação e agrupamento",
      "Documenta a configuração e realiza treinamento do time de TI",
    ],
    clientDoes: [
      "Contratar e manter a VPS onde o Zabbix é instalado",
      "Definir quais servidores e métricas devem ser monitorados",
      "Configurar os limiares de alerta conforme o negócio",
      "Gerenciar os acessos dos administradores de TI",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação do servidor Zabbix",
        description:
          "A PaperMoon instala o Zabbix Server na sua VPS com banco PostgreSQL e interface web configurada. Definimos as credenciais e o acesso HTTPS.",
      },
      {
        num: "02",
        title: "Agentes nos servidores",
        description:
          "Instalamos o agente Zabbix nos servidores que você quer monitorar — físicos, VMs ou cloud. Configuramos as métricas: CPU, memória, disco, serviços HTTP/S, latência e outros.",
      },
      {
        num: "03",
        title: "Alertas e dashboards",
        description:
          "Quando qualquer métrica cruza o limiar configurado, o Zabbix dispara alertas por e-mail com detalhes do problema, gravidade e identificação do host. Dashboards configuráveis deixam tudo visível em tempo real.",
      },
    ],
    featureGroups: [
      {
        title: "Monitoramento",
        items: [
          "Servidores Linux, Windows e macOS",
          "Serviços web (HTTP/S, APIs, endpoints)",
          "Banco de dados (PostgreSQL, MySQL, Redis)",
          "Rede: latência, perda de pacotes, interfaces",
          "Contêineres Docker e clusters Kubernetes",
        ],
      },
      {
        title: "Alertas",
        items: [
          "Alertas por e-mail com detalhes do problema e gravidade",
          "Escalação: nível 1 → nível 2 se não resolvido",
          "Agrupamento de alertas para evitar flood",
          "Alertas de recuperação quando o problema é resolvido",
        ],
      },
      {
        title: "Visualização",
        items: [
          "Dashboards customizáveis por equipe",
          "Gráficos históricos de qualquer métrica",
          "Mapas de topologia de rede",
          "Relatórios de disponibilidade e SLA",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "A cobrança é mensal ou única?",
        a: "A implantação do Zabbix é cobrada como projeto único — sem mensalidade. Você paga uma vez pela instalação, configuração dos agentes, triggers e dashboards. Adição de novos hosts e ajustes futuros são contratados sob demanda, via invoice avulsa.",
      },
      {
        q: "Posso monitorar servidores em qualquer provedor?",
        a: "Sim. O agente Zabbix roda em qualquer servidor Linux ou Windows, independente do provedor (AWS, Azure, GCP, Hostinger, servidores físicos). O único requisito é conectividade de rede entre o agente e o servidor Zabbix.",
      },
      {
        q: "Posso contratar Zabbix e GLPI juntos?",
        a: "Sim. O Zabbix e o GLPI podem ser implantados em conjunto na mesma VPS ou em VPSs separadas. A contratação conjunta é comum em equipes de TI que querem monitoramento e helpdesk na mesma plataforma. Integrações adicionais entre os sistemas podem ser contratadas separadamente.",
      },
      {
        q: "Quantos hosts o Zabbix consegue monitorar?",
        a: "O Zabbix é altamente escalável. A mesma instalação que monitora 10 servidores pode ser expandida para monitorar centenas ou milhares sem mudar a licença — é open-source. Para grandes ambientes (500+ hosts), recomendamos VPS mais robusto (8+ vCPU, 16+ GB RAM) e banco de dados otimizado. A PaperMoon dimensiona a infraestrutura conforme o volume do cliente.",
      },
      {
        q: "Posso receber alertas do Zabbix no WhatsApp ou Telegram?",
        a: "Sim. O Zabbix suporta alertas via e-mail, Telegram, Slack, Teams e qualquer endpoint HTTP (webhook). Para WhatsApp, integramos via n8n: quando o Zabbix dispara um alerta, o n8n recebe o webhook e envia a mensagem no WhatsApp do plantão. A PaperMoon configura o canal de alerta preferido da sua equipe.",
      },
    ],
    prerequisites: [
      "VPS dedicada para o servidor Zabbix com Ubuntu 22.04 (mínimo 2 vCPU, 4 GB RAM, 60 GB SSD)",
      "Acesso SSH a todos os servidores e hosts a serem monitorados",
      "Lista de hosts, serviços e métricas críticas a monitorar",
      "Contatos de alerta (e-mail, WhatsApp ou Telegram)",
      "Portas 10050/10051 liberadas no firewall entre agentes e servidor Zabbix",
    ],
  },
  /* ── Proxmox VE ─────────────────────────────────────────────────── */
  {
    slug: "proxmox",
    name: "Proxmox VE",
    tagline: "Virtualização enterprise open-source instalada no seu servidor.",
    description:
      "Implantação completa do Proxmox Virtual Environment no seu servidor dedicado ou bare-metal. VMs, containers LXC, storage ZFS, backup agendado e painel web completo.",
    about:
      "O Proxmox VE (Virtual Environment) é desenvolvido desde 2008 pela empresa austríaca Proxmox Server Solutions e se tornou a plataforma de virtualização open-source mais adotada em pequenas e médias empresas. Combina dois motores de virtualização em uma única interface web: o KVM (Kernel-based Virtual Machine) para virtualização completa de qualquer sistema operacional, e o LXC (Linux Containers) para workloads mais leves que não precisam de uma VM dedicada.\n\nO que torna o Proxmox relevante é o que ele oferece sem custo de licença: alta disponibilidade (HA) com failover automático entre nodes, storage distribuído via Ceph, live migration de VMs sem downtime, backup integrado com o Proxmox Backup Server e uma API REST completa para automação via Terraform ou Ansible. Ferramentas equivalentes da VMware chegam a custar 5 vezes mais em licenciamento.\n\nA PaperMoon realiza a instalação do Proxmox de forma presencial — um técnico vai ao local do servidor, configura o ambiente de boot, a rede de gerenciamento, o storage ZFS e as VMs iniciais. Treinamos a equipe de TI para operar com autonomia: criação de VMs, snapshots, restore e expansão do cluster.",
    differentials: [
      "Virtualização enterprise sem custo de licença — VMware custa até 5× mais pelo mesmo recurso",
      "KVM e LXC em uma interface única: VMs completas e containers no mesmo painel",
      "Alta disponibilidade (HA) e live migration incluídos, sem licença adicional",
      "Instalação presencial com configuração de ZFS, VLANs e VMs iniciais já no dia da entrega",
      "Treinamento completo da equipe de TI para operar sem depender da PaperMoon no dia a dia",
    ],
    comingSoon: false,
    icon: Server,
    ...SERVICE_TONES.warning,
    heroImage: null,
    heroImageAlt: "Proxmox VE — painel de gerenciamento de virtualização",
    metaTitle: "Proxmox VE — Virtualização instalada no seu servidor — PaperMoon",
    metaDescription:
      "A PaperMoon implanta o Proxmox VE no seu servidor: VMs KVM, containers LXC, ZFS, backup agendado e cluster HA. Implantação única com treinamento.",
    papermoonDoes: [
      "Instala e configura o Proxmox VE no servidor dedicado",
      "Configura pools de storage (ZFS, LVM ou Ceph conforme hardware)",
      "Cria as VMs e containers LXC iniciais conforme a necessidade",
      "Configura rede interna (SDN), VLANs e acesso seguro ao painel",
      "Implementa rotina de backup agendado (Proxmox Backup Server ou remoto)",
      "Documenta a infraestrutura e realiza treinamento da equipe de TI",
    ],
    clientDoes: [
      "Fornecer servidor dedicado ou bare-metal e agendar visita presencial para a instalação",
      "Definir quais VMs e serviços serão criados inicialmente",
      "Gerenciar VMs e containers no dia a dia após o treinamento",
      "Contratar storage adicional se necessário (NFS, SAN, etc.)",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação do Proxmox VE",
        description:
          "A instalação do Proxmox VE é realizada de forma presencial: um técnico da PaperMoon vai até o local onde o servidor está instalado, realiza o boot pelo pendrive, instala o Proxmox VE, configura a rede de gerenciamento e o painel web com HTTPS. Definimos senhas, usuários e políticas de acesso.",
      },
      {
        num: "02",
        title: "Storage, rede e VMs",
        description:
          "Configuramos os pools de storage (ZFS para redundância, LVM para performance), criamos as VMs e containers LXC conforme seu inventário, e configuramos as VLANs e redes internas necessárias.",
      },
      {
        num: "03",
        title: "Backup, HA e treinamento",
        description:
          "Implementamos a rotina de backup agendado, configuramos alertas de utilização e realizamos o treinamento da equipe: criar VMs, snapshots, migração live, restore e gestão do cluster.",
      },
    ],
    featureGroups: [
      {
        title: "Virtualização",
        items: [
          "VMs KVM com suporte a Windows, Linux e qualquer SO",
          "Containers LXC para serviços mais leves e rápidos",
          "Snapshots e clones em segundos",
          "Live migration entre nodes do cluster sem downtime",
          "CPU e memória configuráveis por VM individualmente",
        ],
      },
      {
        title: "Storage e backup",
        items: [
          "ZFS com RAID-Z para redundância e integridade de dados",
          "Ceph para storage distribuído em clusters maiores",
          "Backup agendado com retenção configurável",
          "Restore granular: VM inteira ou arquivo específico",
          "Replicação para servidor remoto (disaster recovery)",
        ],
      },
      {
        title: "Gestão e rede",
        items: [
          "Painel web completo — sem linha de comando para operações rotineiras",
          "API REST para automação e integração com IaC (Terraform)",
          "SDN para redes virtuais e VLANs isoladas",
          "Alta disponibilidade (HA) com failover automático",
          "Controle de acesso por usuário e permissão granular",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "A cobrança é mensal ou única?",
        a: "A implantação do Proxmox é cobrada como projeto único — sem mensalidade. Você paga uma vez pela instalação, configuração e treinamento. Expansões futuras (novos nodes, VMs, integrações) são contratadas sob demanda.",
      },
      {
        q: "Que tipo de servidor preciso ter?",
        a: "O Proxmox VE roda em qualquer servidor x86-64 com suporte a virtualização (Intel VT-x / AMD-V habilitado). Para uso produtivo, recomendamos no mínimo 32 GB RAM e discos SSD. Servidores dedicados (Hetzner, OVH, Contabo) funcionam muito bem. Consulte nossa equipe para avaliar o hardware disponível.",
      },
      {
        q: "Posso montar um cluster com múltiplos servidores?",
        a: "Sim. O Proxmox suporta clusters de até centenas de nodes com alta disponibilidade (HA). A PaperMoon configura o cluster, a rede de corosync e as políticas de failover automático. Para storage compartilhado em cluster, utilizamos Ceph ou NFS.",
      },
      {
        q: "Vocês oferecem treinamento após a implantação?",
        a: "Sim. O treinamento está incluído no escopo. Após a entrega, realizamos sessões com a equipe de TI cobrindo: criação e gerenciamento de VMs, snapshots, restore de backup, migração live e monitoramento de recursos. O número de sessões é definido no momento da contratação.",
      },
      {
        q: "O Proxmox VE tem custo de licença?",
        a: "O Proxmox VE é open-source e gratuito — pode ser instalado e usado sem pagar nenhuma licença. A Proxmox Server Solutions oferece assinaturas de suporte empresarial opcional com atualizações de repositório Enterprise, mas elas não são obrigatórias. A PaperMoon instala o Proxmox com repositório community (gratuito) ou Enterprise conforme a preferência do cliente.",
      },
    ],
    prerequisites: [
      "Servidor bare-metal dedicado com processador x86-64 compatível com virtualização (Intel VT-x / AMD-V)",
      "Mínimo 32 GB RAM e 2 discos SSD (um para o sistema, um ou mais para VMs)",
      "Acesso físico ou KVM-over-IP ao servidor para a instalação",
      "Rede local com switch gerenciável para configuração de VLANs (recomendado)",
    ],
  },

  /* ── TrueNAS ─────────────────────────────────────────────────────── */
  {
    slug: "truenas",
    name: "TrueNAS",
    tagline: "Storage centralizado open-source com ZFS na sua rede.",
    description:
      "Implantação do TrueNAS na sua rede local ou servidor dedicado: armazenamento centralizado ZFS, replicação, snapshots agendados e compartilhamento NFS/SMB para toda a equipe.",
    about:
      "O TrueNAS é descendente direto do FreeNAS, lançado em 2005 como o primeiro sistema operacional open-source focado exclusivamente em armazenamento NAS baseado em FreeBSD. Desde 2011 é desenvolvido e mantido pela iXsystems, empresa californiana especializada em storage enterprise. Hoje o projeto possui duas versões: TrueNAS CORE (FreeBSD, mais maduro) e TrueNAS SCALE (baseado em Debian Linux, com suporte a containers e apps).\n\nO grande diferencial do TrueNAS é o sistema de arquivos ZFS — desenvolvido pela Sun Microsystems e considerado o sistema de arquivos mais confiável para armazenamento de dados. O ZFS usa checksums automáticos em todos os blocos de dados, detectando e corrigindo silenciosamente erros de hardware antes que causem corrupção. Diferente do RAID tradicional, o ZFS garante a integridade dos dados mesmo após falhas de disco simultâneas.\n\nA PaperMoon implanta o TrueNAS no hardware dedicado do cliente — um servidor com múltiplos discos ou um NAS dedicado — configura os pools de armazenamento com a redundância ideal (RAID-Z1, Z2 ou Z3 conforme o nível de risco aceitável), cria os datasets com quotas por departamento e ativa o compartilhamento NFS para Linux e SMB para Windows e macOS.",
    differentials: [
      "ZFS com checksums automáticos: proteção contra corrupção silenciosa de dados (bit rot)",
      "Snapshots instantâneos e agendados sem impacto de performance — volte ao estado de ontem em segundos",
      "Replicação para site remoto: backup offsite automático via ZFS send/receive",
      "Integração nativa com Nextcloud para transformar o NAS em nuvem privada de arquivos",
      "Hardware neutro: roda em qualquer servidor com múltiplos discos, sem lock-in de fabricante",
    ],
    comingSoon: false,
    icon: HardDrive,
    ...SERVICE_TONES.info,
    heroImage: null,
    heroImageAlt: "TrueNAS — painel de gerenciamento de storage",
    metaTitle: "TrueNAS — Storage open-source instalado na sua rede — PaperMoon",
    metaDescription:
      "A PaperMoon implanta o TrueNAS na sua rede: ZFS, replicação, snapshots, NFS/SMB e backup centralizado. Implantação única com treinamento.",
    papermoonDoes: [
      "Instala e configura o TrueNAS no hardware ou servidor dedicado",
      "Configura pools ZFS com RAID-Z para redundância e integridade de dados",
      "Cria shares NFS/SMB para acesso da rede local",
      "Configura snapshots agendados com retenção configurável",
      "Implementa replicação para servidor remoto (disaster recovery)",
      "Documenta o ambiente e realiza treinamento da equipe",
    ],
    clientDoes: [
      "Fornecer hardware dedicado ou servidor com discos para o TrueNAS",
      "Definir estrutura de compartilhamentos e permissões por departamento",
      "Gerenciar usuários e permissões de acesso no dia a dia",
      "Monitorar o espaço em disco e saúde dos discos",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação e configuração ZFS",
        description:
          "A PaperMoon instala o TrueNAS no hardware definido e configura os pools ZFS com RAID-Z conforme o número de discos disponíveis. Definimos nome de host, rede de gerenciamento e acesso HTTPS.",
      },
      {
        num: "02",
        title: "Shares, snapshots e replicação",
        description:
          "Criamos os datasets por departamento, configuramos as shares NFS/SMB com permissões por usuário ou grupo, habilitamos snapshots automáticos com retenção e configuramos replicação para backup remoto.",
      },
      {
        num: "03",
        title: "Integração de rede e treinamento",
        description:
          "Integramos o TrueNAS com a rede existente (Active Directory/LDAP se necessário) e treinamos a equipe para gerenciar datasets, shares, snapshots e restaurações de backup pelo painel web.",
      },
    ],
    featureGroups: [
      {
        title: "Storage e confiabilidade",
        items: [
          "ZFS com RAID-Z — proteção contra corrupção de dados",
          "Snapshots automáticos agendados com retenção configurável",
          "Replicação para servidor remoto (disaster recovery)",
          "Compressão e deduplicação automática de dados",
          "Scrub agendado para verificação de integridade",
        ],
      },
      {
        title: "Compartilhamento de arquivos",
        items: [
          "SMB/CIFS para Windows — integração nativa com Explorador de Arquivos",
          "NFS para Linux/macOS e containers",
          "iSCSI para volumes de bloco (VMs, bancos de dados)",
          "Permissões granulares por usuário, grupo ou IP",
          "ACLs compatíveis com Active Directory",
        ],
      },
      {
        title: "Gestão e monitoramento",
        items: [
          "Painel web completo — sem linha de comando para operações rotineiras",
          "Alertas de saúde dos discos (S.M.A.R.T.) por e-mail",
          "Estatísticas de uso por dataset em tempo real",
          "API REST para integração com sistemas de monitoramento",
          "Suporte a plugins e VMs no TrueNAS Scale",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "A cobrança é mensal ou única?",
        a: "A implantação do TrueNAS é cobrada como projeto único — sem mensalidade. Você paga uma vez pela instalação, configuração dos pools ZFS, shares, snapshots e treinamento. Adição de discos, novos datasets e integrações futuras são contratadas sob demanda.",
      },
      {
        q: "Que hardware preciso ter?",
        a: "O TrueNAS roda em servidores x86-64 com múltiplos discos. Para uso produtivo, recomendamos no mínimo 16 GB RAM (o ZFS usa RAM para cache) e discos dedicados (não compartilhados com o sistema operacional). A PaperMoon avalia o hardware disponível e indica a configuração ideal de RAID-Z.",
      },
      {
        q: "Posso usar junto com o Proxmox?",
        a: "Sim. A combinação TrueNAS + Proxmox é muito comum: o TrueNAS fornece o storage compartilhado via NFS ou iSCSI para o cluster Proxmox, que usa o espaço para armazenar discos de VMs e containers. A PaperMoon configura a integração entre os dois sistemas.",
      },
      {
        q: "O TrueNAS substitui um NAS de marca (Synology, QNAP)?",
        a: "Para a maioria dos casos de uso empresarial, sim. O TrueNAS oferece funcionalidades equivalentes ou superiores (ZFS, replicação, iSCSI) sem custo de licença de software — você paga apenas pelo hardware. A principal diferença é que a configuração inicial é mais técnica, por isso a PaperMoon cuida de toda a implantação.",
      },
      {
        q: "Qual a diferença entre TrueNAS CORE e TrueNAS SCALE?",
        a: "TrueNAS CORE é baseado em FreeBSD — mais maduro e estável, ideal para NAS dedicado. TrueNAS SCALE é baseado em Debian Linux — suporta containers Docker e VMs além do storage, ideal para quem quer consolidar NAS e aplicações no mesmo hardware. A PaperMoon recomenda a versão conforme o caso de uso: CORE para storage puro, SCALE para ambientes que precisam de aplicações rodando junto.",
      },
    ],
    prerequisites: [
      "Servidor ou hardware dedicado x86-64 com suporte a ECC RAM (recomendado)",
      "Mínimo 16 GB RAM (ZFS usa memória como cache) e discos dedicados separados do SO",
      "Acesso físico ou remoto (IPMI/iDRAC) para a instalação",
      "Rede local estruturada com capacidade para tráfego de armazenamento (1 Gbps mínimo)",
    ],
  },

  /* ── Nextcloud ───────────────────────────────────────────────────── */
  {
    slug: "nextcloud",
    name: "Nextcloud",
    tagline: "Nuvem privada e colaboração instalada na sua VPS.",
    description:
      "Implantação completa do Nextcloud na sua VPS: armazenamento de arquivos, calendário, contatos, videoconferência e office online — tudo sob controle da sua empresa, sem depender do Google ou Microsoft.",
    about:
      "O Nextcloud nasceu em 2016 como um fork do ownCloud, criado pelo próprio fundador original do projeto, Frank Karlitschek, após divergências sobre o modelo de negócios. Desde então cresceu para se tornar a maior plataforma de colaboração auto-hospedada do mundo, com mais de 400 mil instalações conhecidas e suporte ativo de empresas como Deutsche Telekom, Red Hat e Siemens.\n\nMais do que um simples substituto do Google Drive, o Nextcloud é uma suíte completa: arquivos com versionamento e links de compartilhamento, calendário e contatos sincronizados com qualquer dispositivo, videoconferência via Nextcloud Talk, edição colaborativa de documentos com Nextcloud Office (baseado no LibreOffice), e integração com Active Directory e LDAP para grandes organizações. Para empresas que precisam de conformidade com a LGPD, ter os dados na própria infraestrutura — e não em servidores da Google ou Microsoft — é um requisito não negociável.\n\nA PaperMoon instala o Nextcloud com configuração de produção completa (Nginx, PHP-FPM, Redis para cache de sessão, Let's Encrypt SSL), integra com o armazenamento local ou com o TrueNAS instalado na rede, e configura as contas de usuário com os grupos e permissões conforme a estrutura da empresa.",
    differentials: [
      "Alternativa completa ao Google Workspace e Microsoft 365 — sem mensalidade por usuário",
      "Seus arquivos ficam na sua VPS: conformidade com LGPD sem depender de terceiros",
      "Videoconferência (Talk), edição de documentos (Office) e calendário incluídos na mesma plataforma",
      "Integração com Active Directory/LDAP: login com a mesma credencial de rede",
      "Conexão nativa com TrueNAS para usar o storage NAS como backend de arquivos",
    ],
    comingSoon: false,
    icon: Cloud,
    ...SERVICE_TONES.info,
    heroImage: null,
    heroImageAlt: "Nextcloud — painel de nuvem privada e colaboração",
    metaTitle: "Nextcloud — Nuvem privada instalada na sua VPS — PaperMoon",
    metaDescription:
      "A PaperMoon instala o Nextcloud na sua VPS: arquivos, calendário, contatos, vídeo e office online. Nuvem privada com controle total. Implantação única com treinamento.",
    papermoonDoes: [
      "Instala e configura o Nextcloud na sua VPS (Docker ou nativo)",
      "Configura armazenamento local ou integrado (S3, Minio, NFS)",
      "Instala e parametriza os apps: Talk, Calendar, Contacts, OnlyOffice",
      "Configura SSL, e-mail de notificação e políticas de segurança",
      "Migra arquivos existentes (Google Drive, OneDrive, pasta local)",
      "Documenta o ambiente e realiza treinamento da equipe",
    ],
    clientDoes: [
      "Contratar e manter a VPS onde o Nextcloud é instalado",
      "Definir políticas de compartilhamento e acesso por usuário",
      "Gerenciar usuários e grupos no dia a dia após o treinamento",
      "Contratar storage adicional conforme o crescimento dos dados",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação e configuração base",
        description:
          "A PaperMoon instala o Nextcloud na sua VPS com banco PostgreSQL, Redis para cache e HTTPS configurado. Definimos cotas de armazenamento, políticas de senha e domínio personalizado.",
      },
      {
        num: "02",
        title: "Apps e integrações",
        description:
          "Instalamos e configuramos os apps conforme sua necessidade: Nextcloud Talk (videoconferência), Calendar, Contacts, OnlyOffice ou Collabora para edição de documentos online, e integração com armazenamento externo.",
      },
      {
        num: "03",
        title: "Migração e treinamento",
        description:
          "Migramos seus arquivos do Drive, OneDrive ou servidor atual. Após a entrega, treinamos a equipe no uso do Nextcloud desktop, mobile e web — garantindo autonomia completa.",
      },
    ],
    featureGroups: [
      {
        title: "Arquivos e sincronização",
        items: [
          "Sync automático para desktop (Windows, macOS, Linux)",
          "App mobile (iOS e Android) para acesso offline",
          "Compartilhamento com link, senha e prazo de validade",
          "Versionamento de arquivos com histórico de alterações",
          "Suporte a WebDAV para integração com ferramentas externas",
        ],
      },
      {
        title: "Colaboração",
        items: [
          "Nextcloud Talk — videoconferência e chat interno",
          "Calendário compartilhado por equipe com sincronização CalDAV",
          "Agenda de contatos com CardDAV",
          "Edição colaborativa de documentos (OnlyOffice ou Collabora)",
          "Kanban e formulários internos",
        ],
      },
      {
        title: "Segurança e controle",
        items: [
          "Todos os dados ficam na sua VPS — sem Google, sem Microsoft",
          "Autenticação em dois fatores (TOTP, WebAuthn)",
          "Integração opcional com Active Directory / LDAP",
          "Logs de auditoria: quem acessou, baixou ou compartilhou o quê",
          "Criptografia ponta a ponta para pastas sensíveis",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "A cobrança é mensal ou única?",
        a: "A implantação do Nextcloud é cobrada como projeto único — sem mensalidade. Você paga uma vez pela instalação, configuração, migração de dados e treinamento. Suporte técnico posterior é contratado sob demanda.",
      },
      {
        q: "Quantos usuários posso ter?",
        a: "Não há limite de usuários — o Nextcloud é instalado na sua VPS e o limite real é a capacidade do servidor. Para equipes de até 50 usuários, um VPS de 4 vCPUs e 8 GB RAM com SSD é suficiente. Para mais usuários ou volumes maiores, orientamos a configuração ideal.",
      },
      {
        q: "É possível migrar meus arquivos do Google Drive?",
        a: "Sim. A PaperMoon realiza a migração dos arquivos existentes (Google Drive, OneDrive, Dropbox ou servidor local) durante a implantação. A migração mantém a estrutura de pastas e, quando possível, o histórico de versões.",
      },
      {
        q: "Vocês oferecem treinamento após a implantação?",
        a: "Sim. O treinamento está incluído no escopo. Cobrimos: uso do cliente desktop e mobile, compartilhamento de arquivos, videoconferência com o Talk, calendário compartilhado e edição de documentos online. O número de sessões é definido na contratação.",
      },
      {
        q: "O Nextcloud funciona no celular?",
        a: "Sim. O Nextcloud tem apps oficiais para iOS e Android que sincronizam arquivos offline, acessam o calendário, contatos e câmera do Nextcloud Talk para videoconferência. Os apps são gratuitos e se conectam diretamente ao seu servidor — sem passar por nuvem de terceiros.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 2 vCPU, 4 GB RAM, 80 GB SSD — escalar conforme volume de arquivos)",
      "Domínio próprio com acesso ao painel DNS para apontar subdomínio",
      "Acesso SSH à VPS com usuário root ou sudo",
    ],
  },

  /* ── AAPanel ─────────────────────────────────────────────────────── */
  {
    slug: "aapanel",
    name: "AAPanel",
    tagline: "Painel web para hospedar sites e gerenciar servidores com facilidade.",
    description:
      "Implantação completa do AAPanel (aaPanel) na sua VPS: stack LEMP/LAMP, múltiplos sites, PHP multi-versão, SSL automático, banco de dados e backups — tudo gerenciado por uma interface web intuitiva.",
    about:
      "O aaPanel (baota.com no mercado chinês) foi desenvolvido pela Baota Internet Technology e lançado internacionalmente em 2018 como alternativa gratuita ao cPanel e ao Plesk — ferramentas tradicionais de hospedagem que cobram licenças anuais de R$ 600 a R$ 3.000. Hoje gerencia mais de 6 milhões de servidores em todo o mundo e é amplamente adotado por agências digitais, desenvolvedores freelancers e empresas que precisam hospedar múltiplos sites em um único servidor sem custo de licença.\n\nO aaPanel resolve o principal problema do gerenciamento de servidores web: a complexidade de instalar e manter manualmente Nginx, Apache, PHP, MySQL, SSL e FTP — tarefas que exigem conhecimento avançado de Linux. Com o aaPanel, todas essas operações são realizadas via interface web com poucos cliques, incluindo instalação de aplicações como WordPress, Joomla ou Laravel com um único botão.\n\nA PaperMoon instala o aaPanel na VPS do cliente, configura a stack inicial (Nginx + PHP + MySQL ou MariaDB), implanta os primeiros sites, emite os certificados SSL e configura as rotinas de backup automático para armazenamento local ou remoto (FTP, S3). Realizamos treinamento para que a equipe do cliente gerencie novos sites e usuários com autonomia.",
    differentials: [
      "Zero custo de licença — nenhuma anuidade versus R$ 600+/ano do cPanel ou Plesk",
      "Múltiplos sites no mesmo servidor com domínios, PHPs e bancos de dados isolados",
      "Instalação com 1 clique: WordPress, Laravel, PrestaShop e mais de 30 aplicações",
      "SSL automático via Let's Encrypt com renovação sem intervenção manual",
      "Interface em português com painel FTP, banco de dados e monitor de recursos no mesmo lugar",
    ],
    comingSoon: false,
    icon: LayoutDashboard,
    ...SERVICE_TONES.success,
    heroImage: null,
    heroImageAlt: "AAPanel — painel de controle web para servidores Linux",
    metaTitle: "AAPanel — Painel de hospedagem instalado na sua VPS — PaperMoon",
    metaDescription:
      "A PaperMoon instala o AAPanel na sua VPS: Nginx, PHP, MySQL, SSL automático e múltiplos sites. Alternativa open-source ao cPanel. Implantação com treinamento.",
    papermoonDoes: [
      "Instala e configura o AAPanel na sua VPS (Ubuntu ou CentOS)",
      "Configura a stack web: Nginx + PHP (multi-versão) + MySQL/MariaDB",
      "Cria os sites e vhosts iniciais com SSL (Let's Encrypt automático)",
      "Aplica hardening de segurança: firewall, fail2ban e WAF",
      "Configura rotina de backup automático dos sites e banco de dados",
      "Documenta o ambiente e realiza treinamento da equipe",
    ],
    clientDoes: [
      "Contratar e manter a VPS onde o AAPanel é instalado",
      "Fornecer domínios e credenciais de DNS para configuração",
      "Gerenciar sites, bancos de dados e atualizações no dia a dia",
      "Monitorar o espaço em disco e recursos do servidor",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação e stack web",
        description:
          "A PaperMoon instala o AAPanel na sua VPS e configura a stack completa: Nginx (ou Apache), PHP nas versões que você precisar, MySQL/MariaDB e Redis. O painel fica acessível em HTTPS com autenticação segura.",
      },
      {
        num: "02",
        title: "Sites, SSL e segurança",
        description:
          "Criamos os vhosts para os domínios existentes, ativamos SSL automático via Let's Encrypt, configuramos o firewall interno, fail2ban contra brute-force e WAF básico para proteger as aplicações.",
      },
      {
        num: "03",
        title: "Backup e treinamento",
        description:
          "Configuramos backups automáticos (diários ou semanais) para armazenamento local ou FTP/S3 remoto. Treinamos sua equipe para gerenciar sites, criar bancos, instalar extensões PHP e restaurar backups pelo painel.",
      },
    ],
    featureGroups: [
      {
        title: "Hospedagem de sites",
        items: [
          "Múltiplos sites no mesmo servidor com vhosts isolados",
          "PHP 7.x, 8.x e múltiplas versões simultâneas por site",
          "SSL automático com Let's Encrypt e renovação automática",
          "Redirecionamentos, regras Nginx e configurações por site",
          "Suporte a WordPress, Laravel, CodeIgniter e qualquer app PHP",
        ],
      },
      {
        title: "Banco de dados e arquivos",
        items: [
          "MySQL/MariaDB com phpMyAdmin integrado",
          "Gerenciador de arquivos visual no painel",
          "FTP com usuários isolados por site",
          "Gerenciamento de cron jobs pela interface",
        ],
      },
      {
        title: "Segurança e backup",
        items: [
          "Firewall de portas gerenciado pelo painel",
          "Fail2ban integrado para proteção contra brute-force",
          "WAF básico (ModSecurity) para proteção das aplicações",
          "Backup agendado de sites e bancos para armazenamento remoto",
          "Monitoramento de recursos: CPU, memória, disco e rede",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "A cobrança é mensal ou única?",
        a: "A implantação do AAPanel é cobrada como projeto único — sem mensalidade. Você paga uma vez pela instalação, configuração, hardening de segurança e treinamento. Suporte técnico posterior (ajustes, novos sites, atualizações) é contratado sob demanda.",
      },
      {
        q: "AAPanel é gratuito. Por que contratar a PaperMoon?",
        a: "O AAPanel é gratuito para instalar, mas a configuração segura e profissional exige experiência: hardening do servidor, configuração correta de Nginx e PHP, fail2ban, WAF, backup remoto e SSL. Erros de configuração podem deixar o servidor vulnerável ou sites fora do ar. A PaperMoon entrega o ambiente configurado corretamente e documentado para a sua operação.",
      },
      {
        q: "Consigo migrar sites de outro servidor?",
        a: "Sim. A PaperMoon faz a migração completa: arquivos, bancos de dados, configurações de e-mail e DNS. O processo é feito com zero ou mínimo downtime usando snapshot/sync antes do corte final.",
      },
      {
        q: "Vocês oferecem treinamento após a implantação?",
        a: "Sim. O treinamento está incluído no escopo. Ensinamos como criar e gerenciar sites, bancos de dados, contas FTP, instalar extensões PHP, configurar cron jobs e restaurar backups pelo painel do AAPanel.",
      },
      {
        q: "O AAPanel suporta múltiplos domínios no mesmo servidor?",
        a: "Sim. Um dos principais pontos fortes do AAPanel é justamente hospedar múltiplos sites no mesmo servidor — cada domínio tem seu próprio vhost, versão de PHP, banco de dados e certificado SSL, completamente isolados uns dos outros. Não há limite de domínios além da capacidade do servidor.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS ou CentOS 7/8 (mínimo 1 vCPU, 1 GB RAM, 20 GB SSD)",
      "Acesso SSH à VPS com usuário root",
      "IP estático ou domínio para acesso ao painel de controle",
    ],
  },

  /* ── WhatsApp via Evolution API ─────────────────────────────────── */
  {
    slug: "whatsapp-evolution",
    name: "WhatsApp via Evolution API",
    tagline: "Chatwoot multiagente + n8n + Evolution API self-hosted na sua VPS.",
    description:
      "Conecte um ou vários números de WhatsApp com a Evolution API, filtre fluxos no n8n e gerencie tudo no Chatwoot. Instalação completa na sua VPS — sem custo por mensagem cobrado pela PaperMoon.",
    about:
      "Para empresas que não se qualificam imediatamente para a API oficial da Meta — como números pré-pagos, contas ainda não verificadas ou equipes que precisam de uma alternativa self-hosted sem depender da aprovação inicial da Meta — a Evolution API conectada ao WhatsApp Web é uma das soluções mais completas disponíveis no mercado brasileiro.\n\nDiferente do WhatsApp Business app (que limita a um dispositivo), a Evolution API permite múltiplas instâncias WhatsApp em um único servidor, cada uma com seu próprio número, todas integradas ao Chatwoot para atendimento multiagente e ao n8n para automação de fluxos. A solução roda inteiramente na VPS do cliente — seus dados de atendimento nunca passam por servidores de terceiros.\n\nA PaperMoon entrega o stack completo na sua VPS: Evolution API + Chatwoot + n8n, todos configurados e integrados entre si. Fluxos de qualificação, bot de FAQ, roteamento por departamento e histórico completo de conversas por contato — preparados conforme a operação do cliente. E quando sua empresa se qualificar para a API oficial da Meta, a PaperMoon realiza a migração sem perda de histórico.",
    differentials: [
      "Stack completo entregue pronto: Evolution API + Chatwoot + n8n já integrados",
      "Múltiplos números WhatsApp em um único servidor, cada um com fluxos independentes",
      "Independente da aprovação inicial da Meta Business Manager para começar a estruturar a operação",
      "Caminho de migração garantido para a API oficial Meta quando a empresa se qualificar",
      "Sem custo por mensagem cobrado pela PaperMoon — a cobrança é pela implantação",
    ],
    comingSoon: false,
    icon: MessageCircle,
    ...SERVICE_TONES.success,
    heroImage: null,
    heroImageAlt: "WhatsApp via Evolution API — múltiplas instâncias no painel",
    metaTitle: "WhatsApp via Evolution API — PaperMoon",
    metaDescription:
      "A PaperMoon instala Evolution API + Chatwoot + n8n na sua VPS: múltiplas instâncias WhatsApp, automação com n8n e atendimento multiagente. Assinatura mensal.",
    papermoonDoes: [
      "Instala e configura Evolution API, Chatwoot e n8n na sua VPS",
      "Conecta as instâncias WhatsApp via QR Code e configura reconexão automática",
      "Cria os fluxos iniciais de triagem e automação no n8n",
      "Integra a Evolution API com o Chatwoot para atendimento multiagente",
      "Documenta o ambiente e treina a equipe",
      "Suporte mensal incluso durante toda a assinatura",
    ],
    clientDoes: [
      "Contratar e manter a VPS onde os serviços são instalados",
      "Fornecer os números de WhatsApp que serão conectados",
      "Respeitar os limites de mensagens para evitar bloqueio do número",
      "Gerenciar instâncias e reconexões no dia a dia",
    ],
    steps: [
      {
        num: "01",
        title: "Contrate uma VPS",
        description:
          "Você contrata um servidor (Hostinger, HostGator, AWS...) e nos passa o acesso SSH. Indicamos as especificações mínimas conforme o volume de mensagens esperado.",
      },
      {
        num: "02",
        title: "Instalamos tudo na sua VPS",
        description:
          "A PaperMoon instala e configura Evolution API, Chatwoot e n8n. Conectamos suas instâncias WhatsApp via QR Code, configuramos reconexão automática e criamos os primeiros fluxos no n8n.",
      },
      {
        num: "03",
        title: "Treinamento e suporte contínuo",
        description:
          "Treinamos sua equipe para gerenciar instâncias, criar fluxos no n8n e atender no Chatwoot. O suporte mensal incluso garante que o ambiente continue funcionando.",
      },
    ],
    featureGroups: [
      {
        title: "WhatsApp e mensagens",
        items: [
          "Múltiplas instâncias WhatsApp em um único servidor",
          "Envio de texto, imagens, documentos, áudio e vídeo",
          "Reconexão automática em caso de queda",
          "Sem custo por mensagem (diferente da API oficial Meta)",
          "Grupos, listas de transmissão e reações",
        ],
      },
      {
        title: "Automação com n8n",
        items: [
          "Fluxos de triagem antes de chegar ao agente",
          "Bot de perguntas frequentes 24/7",
          "Roteamento por palavra-chave, horário ou departamento",
          "Integração com CRM, planilhas e sistemas internos",
          "Configuração personalizada por cliente",
        ],
      },
      {
        title: "Atendimento com Chatwoot",
        items: [
          "Múltiplos agentes no mesmo número WhatsApp",
          "Transferência e atribuição de conversas",
          "Etiquetas, notas internas e histórico completo",
          "Métricas de SLA e desempenho por agente",
          "Canned responses para respostas rápidas",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença do plano WhatsApp via API Meta?",
        a: "A Evolution API usa o protocolo WhatsApp Web (não oficial), sem necessidade de aprovação da Meta e sem custo por mensagem. Mais agilidade para automações internas e menor custo operacional. A contrapartida é o risco de bloqueio do número em uso intenso. Para atendimento comercial em maior escala com total segurança, recomendamos o plano WhatsApp via API Meta (oficial).",
      },
      {
        q: "A cobrança é mensal?",
        a: "Sim. A assinatura mensal inclui instalação, configuração, manutenção e suporte do ambiente completo (Evolution API + Chatwoot + n8n) na sua VPS. Não há custo por mensagem cobrado pela PaperMoon.",
      },
      {
        q: "Posso usar vários números no mesmo servidor?",
        a: "Sim. A Evolution API suporta múltiplas instâncias WhatsApp no mesmo servidor. A PaperMoon configura o número de instâncias acordado na contratação e pode ampliar conforme a demanda cresce.",
      },
      {
        q: "O que acontece se o número for bloqueado?",
        a: "A PaperMoon orienta sobre limites seguros de volume e boas práticas para minimizar o risco. Em caso de bloqueio, auxiliamos na reconexão e na revisão dos fluxos. A responsabilidade pelo uso adequado do número é do cliente.",
      },
      {
        q: "Posso usar vários atendentes com a Evolution API no Chatwoot?",
        a: "Sim. Toda a stack entregue pela PaperMoon (Evolution API + Chatwoot + n8n) suporta múltiplos agentes atendendo os números conectados. O Chatwoot distribui as conversas por agente ou equipe, com atribuição manual ou automática. Não há limite de agentes — o limite real é a capacidade do servidor.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 2 vCPU, 4 GB RAM, 40 GB SSD)",
      "Domínio próprio com acesso ao painel DNS para apontar subdomínio",
      "Acesso SSH à VPS com usuário root ou sudo",
      "Números de WhatsApp disponíveis para escanear o QR Code de ativação",
    ],
  },

  /* ── Evolution API ───────────────────────────────────────────────── */
  {
    slug: "evolution-api",
    name: "Evolution API",
    tagline: "API WhatsApp self-hosted para automação via n8n e Chatwoot.",
    description:
      "Implantação da Evolution API na sua VPS: múltiplas instâncias WhatsApp, webhooks, integração nativa com n8n e Chatwoot. Ideal para automações internas, bots e disparos de baixo volume.",
    about:
      "A Evolution API é um projeto open-source brasileiro criado em 2022 pelo desenvolvedor Davidson Gomes e mantido por uma comunidade ativa no GitHub. Surgiu como resposta à falta de uma solução nacional robusta para quem precisava de um gateway WhatsApp self-hosted com recursos enterprise: múltiplas instâncias, webhooks granulares por evento, suporte a TypeBot e integração nativa com as principais ferramentas de automação do mercado.\n\nO que torna a Evolution API relevante é sua profundidade de integração: cada instância WhatsApp pode ter webhooks independentes configurados por tipo de evento (mensagem recebida, status de entrega, mudança de grupo), o que a torna ideal como camada de backend para bots, sistemas de notificação e plataformas de atendimento. A API RESTful bem documentada facilita integrações customizadas com sistemas internos das empresas.\n\nA PaperMoon instala a Evolution API em servidor dedicado na VPS do cliente, configura as instâncias necessárias e realiza a integração completa com o n8n (para fluxos de automação) e o Chatwoot (para handoff ao atendimento humano). A combinação das três ferramentas na mesma VPS forma um stack de atendimento completo e auto-hospedado.",
    differentials: [
      "Projeto 100% brasileiro — documentação, comunidade e suporte em português",
      "Webhooks granulares por tipo de evento: configure reações diferentes para cada ação do WhatsApp",
      "Integração nativa com n8n e Chatwoot — stack completo de atendimento em uma única VPS",
      "TypeBot integrado para bots conversacionais avançados com menus, perguntas e condições",
      "Código aberto e auditável: nenhuma caixa-preta entre sua empresa e o gateway WhatsApp",
    ],
    comingSoon: false,
    icon: MessageCircle,
    ...SERVICE_TONES.success,
    heroImage: null,
    heroImageAlt: "Evolution API — painel de gerenciamento de instâncias WhatsApp",
    metaTitle: "Evolution API — WhatsApp self-hosted instalado na sua VPS — PaperMoon",
    metaDescription:
      "A PaperMoon instala a Evolution API na sua VPS: múltiplas instâncias, webhooks, integração com n8n e Chatwoot. Automação WhatsApp com controle total.",
    papermoonDoes: [
      "Instala e configura a Evolution API na sua VPS",
      "Conecta as instâncias WhatsApp via QR Code e configura reconexão automática",
      "Integra com o n8n para automação de fluxos de mensagens",
      "Integra com o Chatwoot para atendimento multiagente",
      "Configura webhooks para recebimento de eventos em tempo real",
      "Documenta o ambiente e realiza treinamento da equipe",
    ],
    clientDoes: [
      "Contratar e manter a VPS onde a Evolution API é instalada",
      "Fornecer os números de WhatsApp que serão conectados",
      "Gerenciar as instâncias e reconexões no dia a dia",
      "Respeitar os limites de mensagens para evitar bloqueio do número",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação e configuração",
        description:
          "A PaperMoon instala a Evolution API na sua VPS com banco de dados, Redis para filas e painel de administração protegido por senha. Configuramos o endpoint da API e as chaves de acesso.",
      },
      {
        num: "02",
        title: "Instâncias e integrações",
        description:
          "Criamos as instâncias WhatsApp, escaneamos o QR Code para conexão e configuramos reconexão automática. Integramos com o n8n para automações e com o Chatwoot para atendimento humano quando necessário.",
      },
      {
        num: "03",
        title: "Webhooks e treinamento",
        description:
          "Configuramos os webhooks para eventos (mensagem recebida, status de entrega, conexão) e treinamos sua equipe para gerenciar instâncias, criar fluxos no n8n e monitorar o status das conexões.",
      },
    ],
    featureGroups: [
      {
        title: "Instâncias e mensagens",
        items: [
          "Múltiplas instâncias WhatsApp em um único servidor",
          "Envio de texto, imagens, documentos, áudio e vídeo",
          "Envio de mensagens para grupos e listas de transmissão",
          "Reações, edição e exclusão de mensagens",
          "Reconexão automática em caso de queda",
        ],
      },
      {
        title: "Automação",
        items: [
          "Webhooks para cada evento (mensagem, status, conexão)",
          "Integração nativa com n8n para fluxos sem código",
          "Integração com Chatwoot para handoff ao atendimento humano",
          "TypeBot para bots conversacionais avançados",
          "RabbitMQ para filas de alta disponibilidade",
        ],
      },
      {
        title: "Gestão e API",
        items: [
          "API REST completa com documentação Swagger",
          "Painel de administração web para gerenciar instâncias",
          "Logs de mensagens enviadas e recebidas",
          "Suporte a proxy por instância para isolamento de IPs",
          "Controle de sessões e autenticação por API Key",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença da API oficial da Meta?",
        a: "A Evolution API usa o protocolo WhatsApp Web (não oficial), sem necessidade de aprovação da Meta e sem custo por mensagem. Isso traz mais agilidade e liberdade para automações internas. A contrapartida é o risco de bloqueio do número pelo WhatsApp se o uso for identificado como automação em massa. Para atendimento comercial em escala, nossa solução de WhatsApp API (Meta Oficial) é mais segura e estável.",
      },
      {
        q: "A cobrança é mensal ou única?",
        a: "A implantação da Evolution API é cobrada como projeto único — sem mensalidade. Você paga uma vez pela instalação, configuração e treinamento. Novas instâncias, fluxos ou integrações adicionais são contratadas sob demanda.",
      },
      {
        q: "Posso usar junto com o Chatwoot e n8n?",
        a: "Sim, essa é a configuração mais comum. A Evolution API recebe as mensagens do WhatsApp, o n8n processa e filtra automaticamente, e as conversas que precisam de atenção humana são encaminhadas ao Chatwoot. A PaperMoon configura toda essa integração.",
      },
      {
        q: "Vocês oferecem treinamento após a implantação?",
        a: "Sim. O treinamento está incluído no escopo. Ensinamos como criar e gerenciar instâncias, verificar o status de conexão, criar fluxos básicos no n8n integrado à Evolution API e monitorar logs de mensagens.",
      },
      {
        q: "Posso usar a Evolution API para disparos de marketing em massa?",
        a: "A Evolution API não é recomendada para campanhas em massa — o WhatsApp detecta padrões de envio em volume e pode bloquear o número. Para disparos de marketing ou notificações em escala, recomendamos a API oficial da Meta (nosso plano WhatsApp via API Meta), que tem limites maiores e número verificado. A Evolution API é ideal para automação de atendimento, bots e integrações de baixo volume.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 1 vCPU, 2 GB RAM, 20 GB SSD)",
      "Domínio próprio com acesso ao painel DNS para apontar subdomínio",
      "Acesso SSH à VPS com usuário root ou sudo",
      "Números de WhatsApp para ativação das sessões",
    ],
  },
  /* ── Redes corporativas ────────────────────────────────────────── */
  {
    slug: "redes",
    name: "Redes corporativas",
    tagline: "Projeto, implantação e configuração de rede para empresas.",
    description:
      "A PaperMoon projeta e implanta infraestruturas de rede corporativa: switching, roteamento, VLANs, firewall, Wi-Fi empresarial e VPN. Serviço presencial com certificação do ambiente entregue.",
    about:
      "A infraestrutura de rede é a fundação de toda a operação de TI de uma empresa. Redes corporativas bem projetadas garantem que sistemas críticos — ERP, VoIP, câmeras de segurança e servidores — tenham a largura de banda e o isolamento corretos, enquanto redes domésticas improvisadas causam lentidão, falhas de segurança e gargalos que paralisam a operação.\n\nA PaperMoon atua desde o projeto até a entrega certificada: levantamos os requisitos de cada setor (escritório, depósito, sala de reunião, CFTV), desenhamos a topologia com segmentação por VLANs para isolar tráfego crítico do tráfego geral, dimensionamos o hardware de switching e roteamento, configuramos o firewall com políticas de acesso granulares e implantamos o Wi-Fi empresarial com autenticação 802.1X quando necessário.\n\nEntregamos o projeto com documentação completa: diagrama de rede em formato editável, inventário de equipamentos e configurações, e relatório de certificação de cada ponto de rede — essencial para auditoria e futuras expansões. O monitoramento do ambiente pode ser configurado em conjunto com o Zabbix.",
    differentials: [
      "Projeto de rede com cálculo de capacidade por setor — não apenas a ligação dos cabos",
      "Segmentação por VLANs: câmeras, VoIP e servidores isolados do tráfego de usuários",
      "Firewall gerenciado com políticas de acesso entre VLANs e para a internet",
      "Documentação completa: diagrama editável + inventário + certificação de todos os pontos",
      "Integração com Zabbix para monitoramento pró-ativo da rede após a entrega",
    ],
    comingSoon: false,
    icon: Network,
    ...SERVICE_TONES.info,
    heroImage: null,
    heroImageAlt: "Rede corporativa — rack de switches e patch panels",
    metaTitle: "Redes corporativas — projeto e implantação — PaperMoon",
    metaDescription:
      "A PaperMoon projeta e implanta redes corporativas: switching, VLANs, firewall, Wi-Fi empresarial e VPN. Serviço presencial, certificação inclusa.",
    papermoonDoes: [
      "Realiza levantamento técnico do ambiente e propõe o diagrama de rede",
      "Configura switches gerenciáveis (VLANs, STP, LACP)",
      "Implanta e configura roteadores e firewalls (pfSense, MikroTik, Fortinet)",
      "Configura Wi-Fi empresarial com autenticação WPA2-Enterprise ou RADIUS",
      "Implementa VPN site-to-site e acesso remoto seguro",
      "Entrega documentação completa e diagrama lógico/físico da rede",
    ],
    clientDoes: [
      "Fornecer acesso ao local e à infraestrutura elétrica existente",
      "Aprovar o projeto de rede antes do início da execução",
      "Adquirir os equipamentos indicados no projeto (ou solicitar fornecimento à PaperMoon)",
      "Definir VLANs, segmentações e políticas de acesso desejadas",
    ],
    steps: [
      {
        num: "01",
        title: "Levantamento e projeto",
        description:
          "Um técnico da PaperMoon visita o local, mapeia o ambiente, conta pontos de rede existentes e elabora o diagrama lógico e físico da rede. O projeto é apresentado e aprovado antes de qualquer execução.",
      },
      {
        num: "02",
        title: "Implantação e configuração",
        description:
          "Com o projeto aprovado, nossa equipe executa a configuração dos switches, roteadores e firewall — VLANs, QoS, rotas, regras de firewall, Wi-Fi e VPN — tudo devidamente testado antes da entrega.",
      },
      {
        num: "03",
        title: "Certificação e documentação",
        description:
          "Ao final, certificamos a rede, medimos latência e throughput por segmento e entregamos o diagrama atualizado, credenciais e manual de operação para a equipe de TI do cliente.",
      },
    ],
    featureGroups: [
      {
        title: "Switching e roteamento",
        items: [
          "VLANs por departamento, dispositivo ou função",
          "Spanning Tree Protocol (STP/RSTP) para redundância",
          "Link Aggregation (LACP) para maior largura de banda",
          "Roteamento estático e dinâmico (OSPF, BGP quando necessário)",
          "QoS para priorização de VoIP e videoconferência",
        ],
      },
      {
        title: "Segurança e acesso",
        items: [
          "Firewall com regras por VLAN e por usuário",
          "Wi-Fi empresarial WPA2-Enterprise com autenticação RADIUS",
          "VPN SSL e site-to-site para acesso remoto seguro",
          "Segmentação de rede de visitantes (guest network isolada)",
          "Monitoramento de tráfego e alertas de anomalias",
        ],
      },
      {
        title: "Documentação e suporte",
        items: [
          "Diagrama lógico e físico da rede entregue em PDF e Visio",
          "Credenciais e acesso documentados em cofre de senhas",
          "Suporte técnico por 30 dias após a entrega",
          "Treinamento da equipe de TI interna",
          "Expansão e ajustes contratados sob demanda",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "O serviço é presencial?",
        a: "Sim. Redes corporativas exigem presença física no local — levantamento, configuração de equipamentos e certificação são realizados presencialmente pela equipe da PaperMoon. Configurações remotas de equipamentos já instalados podem ser realizadas remotamente.",
      },
      {
        q: "Vocês fornecem os equipamentos (switches, roteadores)?",
        a: "O padrão é o cliente adquirir os equipamentos — indicamos marca e modelo conforme o orçamento e a necessidade. Mas podemos incluir o fornecimento no escopo do projeto mediante cotação.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "Projetos de rede são cobrados por escopo — um valor único pelo levantamento, execução e documentação. Não há mensalidade. Expansões e ajustes futuros são cotados separadamente.",
      },
      {
        q: "Quanto tempo leva a implantação?",
        a: "O cronograma depende do tamanho da rede, da quantidade de pontos, da infraestrutura existente e das janelas de execução disponíveis no cliente. A PaperMoon detalha o plano por fases antes do início da implantação.",
      },
      {
        q: "A PaperMoon instala Wi-Fi empresarial?",
        a: "Sim. Configuramos redes Wi-Fi corporativas com controladora, autenticação WPA2-Enterprise (802.1X + RADIUS), rede de visitantes isolada e cobertura dimensionada por planta baixa. Para grandes áreas, desenhamos o projeto de APs com mapas de calor para garantir sinal uniforme. Trabalhamos com Ubiquiti, TP-Link Omada, Aruba e Mikrotik.",
      },
    ],
    prerequisites: [
      "Planta baixa ou croqui do local com indicação dos pontos de rede desejados",
      "Acesso presencial ao espaço físico para levantamento técnico",
      "Definição dos equipamentos a serem utilizados (switches, roteadores, APs) ou orçamento para aquisição",
      "Contato técnico no local para acompanhar a instalação",
    ],
  },

  /* ── Cabeamento estruturado ────────────────────────────────────── */
  {
    slug: "cabeamento",
    name: "Cabeamento estruturado",
    tagline: "Instalação certificada Cat5e, Cat6 e fibra óptica.",
    description:
      "A PaperMoon instala cabeamento estruturado certificado para redes corporativas: Cat5e, Cat6, Cat6A e fibra óptica. Passagem de cabos, patch panels, identificação e certificação com equipamento homologado.",
    about:
      "O cabeamento estruturado é a espinha dorsal física de qualquer rede corporativa. Diferente do cabeamento improvisado — onde cabos percorrem o ambiente sem identificação, fixação adequada ou margem para expansão — o cabeamento estruturado segue as normas ABNT NBR 14565 (Brasil) e TIA/EIA-568 (padrão internacional), garantindo desempenho, organização e facilidade de manutenção por décadas.\n\nA categoria do cabo define o limite de velocidade e distância: Cat5e suporta até 1 Gbps em 100 metros, Cat6 chega a 10 Gbps em distâncias de até 55 metros, e Cat6A mantém os 10 Gbps em 100 metros com melhor blindagem contra interferências. Para infraestrutura de câmeras de segurança ou conexão entre andares e prédios, a fibra óptica é a escolha certa — imune a interferências eletromagnéticas e com alcance de quilômetros.\n\nA PaperMoon realiza o projeto, a instalação e a certificação do cabeamento com certificador homologado, gerando o laudo técnico por ponto de rede — documento obrigatório para auditorias e necessário para qualquer garantia dos materiais. Cada cabo recebe etiqueta de identificação nas duas extremidades e é organizado no patch panel com numeração padronizada.",
    differentials: [
      "Certificação com laudo técnico por ponto — o padrão exigido por auditorias de TI e seguradoras",
      "Cat6A para 10 Gbps em 100 metros: rede preparada para os próximos 10 anos",
      "Etiquetagem bilateral e numeração padronizada: qualquer técnico encontra qualquer ponto",
      "Patch panel organizado com espaço calculado para expansão planejada",
      "Fibra óptica para interligação de andares e prédios — sem interferência eletromagnética",
    ],
    comingSoon: false,
    icon: Layers,
    ...SERVICE_TONES.neutral,
    heroImage: null,
    heroImageAlt: "Cabeamento estruturado — rack com patch panel organizado",
    metaTitle: "Cabeamento estruturado Cat5e, Cat6 e fibra — PaperMoon",
    metaDescription:
      "A PaperMoon instala cabeamento estruturado certificado: Cat5e, Cat6, Cat6A e fibra óptica. Passagem, patch panels, identificação e certificação com laudo.",
    papermoonDoes: [
      "Realiza o projeto de passagem de cabos com planta baixa do local",
      "Instala cabos Cat5e, Cat6 ou Cat6A em conduítes ou canaletas",
      "Instala e organiza patch panels em rack ou parede",
      "Identifica todos os pontos com etiquetas padronizadas",
      "Realiza a certificação com testador homologado e emite laudo",
      "Organiza e documenta o rack ao final da instalação",
    ],
    clientDoes: [
      "Fornecer acesso ao local, planta baixa e autorização para passagem de cabos",
      "Aprovar o projeto de passagem antes da execução",
      "Definir quantidade e localização dos pontos de rede desejados",
      "Viabilizar acesso a forros, paredes e áreas técnicas conforme necessário",
    ],
    steps: [
      {
        num: "01",
        title: "Levantamento e projeto",
        description:
          "Visitamos o local, medimos distâncias, identificamos trajetórias de passagem e elaboramos o projeto de cabeamento com localização de cada ponto. O projeto é aprovado antes de qualquer execução.",
      },
      {
        num: "02",
        title: "Instalação e organização",
        description:
          "Nossa equipe passa os cabos em conduítes ou canaletas, instala as tomadas RJ-45, monta e organiza o patch panel no rack, identifica cada ponto com etiquetas padronizadas.",
      },
      {
        num: "03",
        title: "Certificação e laudo",
        description:
          "Certificamos cada ponto com testador homologado, verificamos atenuação, NEXT e FEXT conforme a norma, e emitimos o laudo de certificação. A entrega inclui o mapa completo da instalação.",
      },
    ],
    featureGroups: [
      {
        title: "Tipos de cabeamento",
        items: [
          "Cat5e — até 1 Gbps, ideal para redes legadas e expansões",
          "Cat6 — até 10 Gbps em curtas distâncias, padrão atual",
          "Cat6A — 10 Gbps em até 100m, recomendado para novos projetos",
          "Fibra óptica monomodo e multimodo para backbone entre andares",
          "Patch panels e keystones de marcas homologadas",
        ],
      },
      {
        title: "Organização e identificação",
        items: [
          "Etiquetagem padronizada em todos os pontos e patch panels",
          "Organização com guias de cabos e amarrações no rack",
          "Documentação fotográfica de toda a instalação",
          "Mapa de pontos entregue em planilha e PDF",
          "Rack organizado com espaço reservado para expansão",
        ],
      },
      {
        title: "Normas e certificação",
        items: [
          "Instalação conforme ABNT NBR 14565 e EIA/TIA 568",
          "Certificação com testador Fluke ou equivalente homologado",
          "Laudo de certificação entregue para cada ponto",
          "Atenuação, NEXT, FEXT e Return Loss medidos",
          "Rastreabilidade completa: número de série do cabo por ponto",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Vocês instalam em forro rebaixado e laje?",
        a: "Sim. Nossa equipe está preparada para passagem em forro de gesso, forro metálico, laje, parede de alvenaria e drywall. O projeto define a melhor trajetória para cada ambiente.",
      },
      {
        q: "Qual a diferença entre Cat5e, Cat6 e Cat6A?",
        a: "Cat5e suporta até 1 Gbps e é adequado para redes legadas. Cat6 suporta 10 Gbps em curtas distâncias e é o padrão atual. Cat6A suporta 10 Gbps plenos até 100m e é recomendado para instalações novas. A fibra é indicada para backbone entre andares ou prédios.",
      },
      {
        q: "A certificação é obrigatória?",
        a: "Para garantia da instalação e conformidade com normas, sim. A certificação comprova que cada ponto atende aos parâmetros da categoria instalada. Sem ela, não há como garantir o desempenho da rede.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "Cobrado por ponto instalado ou por escopo fechado de projeto. Inclui material (cabos, keystones, patch panel) e mão de obra. O laudo de certificação está incluso. Sem mensalidade.",
      },
      {
        q: "Vocês fazem instalação de fibra óptica?",
        a: "Sim. Instalamos fibra óptica monomodo e multimodo para backbone entre andares, conexão entre prédios e links de alta velocidade no datacenter. Inclui fusão ou conectorização, testes de atenuação e laudo de certificação. Para ambientes com interferência eletromagnética (próximo a motores, geradores ou cabos de alta tensão), a fibra é a única opção confiável.",
      },
    ],
    prerequisites: [
      "Planta baixa ou croqui do local com indicação dos pontos de rede desejados",
      "Acesso presencial ao espaço físico para levantamento técnico",
      "Decisão sobre categoria do cabeamento (Cat5e, Cat6 ou Cat6A)",
      "Acesso aos eletrodutos, forros ou paredes para passagem dos cabos",
    ],
  },

  /* ── Manutenção de servidores ──────────────────────────────────── */
  {
    slug: "manutencao",
    name: "Manutenção de servidores",
    tagline: "Diagnóstico, limpeza e manutenção preventiva e corretiva.",
    description:
      "Manutenção preventiva e corretiva de servidores físicos e computadores corporativos: limpeza interna, troca de componentes, atualização de firmware, reinstalação de sistema operacional e diagnóstico de falhas.",
    about:
      "Servidores físicos e equipamentos de TI degradam com o tempo — acúmulo de poeira nos dissipadores eleva a temperatura dos processadores, capacitores das fontes de alimentação perdem capacidade, discos HDD acumulam setores defeituosos e firmwares desatualizados introduzem vulnerabilidades de segurança. A manutenção preventiva é a diferença entre um equipamento que funciona por 10 anos e outro que falha em 4.\n\nA PaperMoon executa manutenção preventiva e corretiva em servidores físicos (Dell, HP, IBM, Supermicro), computadores corporativos e notebooks. O processo começa com diagnóstico completo: temperatura, velocidade de leitura/escrita dos discos (via S.M.A.R.T.), tensão da memória RAM, estado dos capacitores e logs de eventos do sistema. O relatório é apresentado antes de qualquer intervenção, com orçamento aprovado pelo cliente.\n\nTodo o histórico de intervenções é registrado no GLPI (se já implantado pelo cliente), criando um ciclo virtuoso de manutenção rastreável — quando um técnico abre um chamado, já sabe o que foi feito no servidor anteriormente. Para ambientes com SLA definido, oferecemos contratos de manutenção mensal com visita presencial agendada.",
    differentials: [
      "Diagnóstico completo antes de qualquer intervenção — cliente aprova o orçamento previamente",
      "Registro de todas as intervenções no GLPI para rastreabilidade do histórico técnico",
      "Manutenção preventiva agendada: evitar falhas antes que elas paralisem a operação",
      "Atendimento presencial para servidores físicos e remoto para diagnóstico de software",
      "Relatório técnico entregue ao final de cada intervenção preventiva ou corretiva",
    ],
    comingSoon: false,
    icon: Cpu,
    ...SERVICE_TONES.warning,
    heroImage: null,
    heroImageAlt: "Manutenção de servidor — técnico realizando diagnóstico",
    metaTitle: "Manutenção de servidores e computadores — PaperMoon",
    metaDescription:
      "Manutenção preventiva e corretiva de servidores físicos: limpeza, troca de componentes, firmware, sistema operacional e diagnóstico de falhas.",
    papermoonDoes: [
      "Realiza diagnóstico completo de hardware e software (logs, S.M.A.R.T., memória)",
      "Executa limpeza interna com soprador e produtos antiestáticos",
      "Troca de peças defeituosas: HDs, SSDs, memórias, fontes, ventoinhas",
      "Atualiza BIOS/UEFI e firmware de controladoras RAID e iDRAC/iLO",
      "Reinstala ou migra sistema operacional preservando dados",
      "Documenta o inventário de hardware e o resultado do serviço",
    ],
    clientDoes: [
      "Fornecer acesso ao equipamento (presencial ou via frete para assistência)",
      "Informar os sintomas observados e o histórico de falhas",
      "Aprovar o orçamento de peças antes da substituição",
      "Realizar backup dos dados críticos antes do serviço (ou contratar o serviço de backup PaperMoon)",
    ],
    steps: [
      {
        num: "01",
        title: "Diagnóstico",
        description:
          "Analisamos logs de sistema, saúde dos discos (S.M.A.R.T.), temperatura, memória e componentes. Identificamos a causa raiz da falha ou degradação e apresentamos o relatório antes de qualquer intervenção.",
      },
      {
        num: "02",
        title: "Manutenção e reparos",
        description:
          "Com o diagnóstico aprovado, executamos a manutenção: limpeza interna, troca de componentes defeituosos, atualização de firmware e reinstalação/migração do sistema operacional conforme necessário.",
      },
      {
        num: "03",
        title: "Testes e entrega",
        description:
          "Após a manutenção, realizamos testes de estabilidade (burn-in, stress test, verificação de memória) e entregamos o relatório completo com o estado do equipamento e recomendações preventivas.",
      },
    ],
    featureGroups: [
      {
        title: "Manutenção preventiva",
        items: [
          "Limpeza interna com soprador industrial e antiestático",
          "Verificação e reposição de pasta térmica",
          "Teste de memória (Memtest) e saúde de discos (S.M.A.R.T.)",
          "Atualização de BIOS/UEFI e firmware de componentes",
          "Verificação de temperatura e funcionamento dos coolers",
        ],
      },
      {
        title: "Manutenção corretiva",
        items: [
          "Diagnóstico de falhas de hardware e software",
          "Troca de HDs, SSDs, memórias, fontes e ventoinhas",
          "Substituição de baterias de CMOS e supercapacitores de RAID",
          "Reinstalação de sistema operacional (Windows Server, Linux)",
          "Migração de dados de disco defeituoso para disco novo",
        ],
      },
      {
        title: "Servidores suportados",
        items: [
          "Dell PowerEdge (R-series, T-series)",
          "HP ProLiant (DL-series, ML-series) com iLO",
          "Supermicro e servidores whitebox",
          "Workstations e computadores corporativos",
          "NAS de marcas diversas (Synology, QNAP, TrueNAS)",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "O atendimento é presencial ou posso enviar o equipamento?",
        a: "Ambos. Para servidores em rack instalados no local, realizamos o atendimento presencial. Para computadores, workstations e servidores tower, o cliente pode enviar o equipamento para nossa bancada ou agendamos visita técnica.",
      },
      {
        q: "Vocês garantem a recuperação de dados em disco defeituoso?",
        a: "Realizamos clonagem de disco com setores defeituosos usando ferramentas especializadas (ddrescue, Clonezilla). A taxa de sucesso depende do nível de dano físico. Para casos críticos, recomendamos laboratório especializado em recuperação de dados.",
      },
      {
        q: "Com que frequência devo fazer manutenção preventiva?",
        a: "Recomendamos manutenção preventiva anual para servidores em produção — incluindo limpeza, verificação de discos, atualização de firmware e relatório de saúde. Servidores em ambientes com muita poeira podem exigir semestral.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "Cobrada por visita técnica + hora de trabalho, ou por escopo fechado para projetos maiores. Peças substituídas são cotadas separadamente com aprovação prévia do cliente.",
      },
      {
        q: "A manutenção pode ser contratada de forma periódica ou mensal?",
        a: "Sim. Para empresas que querem garantir a saúde dos servidores de forma contínua, oferecemos contratos de manutenção preventiva mensal ou trimestral com visita agendada. O contrato inclui relatório técnico após cada visita, registro das intervenções no GLPI e priority response em caso de chamado corretivo urgente.",
      },
    ],
    prerequisites: [
      "Acesso SSH ou presencial aos servidores a serem mantidos",
      "Inventário ou lista dos servidores, SOs e serviços em execução",
      "Janela de manutenção combinada com antecedência para serviços críticos",
      "Credenciais de acesso (root/sudo) ou autorização para criação de usuário técnico",
    ],
  },

  /* ── Backup corporativo ────────────────────────────────────────── */
  {
    slug: "backup",
    name: "Backup corporativo",
    tagline: "Política de backup e recuperação de desastres para empresas.",
    description:
      "A PaperMoon projeta e implanta políticas de backup corporativo completas: definição de RPO/RTO, escolha de ferramentas (Veeam, BorgBackup, Restic, Bacula), configuração de jobs, testes de restore e documentação DRP.",
    about:
      "A ausência de backup é uma das causas mais frequentes de falência de pequenas e médias empresas após incidentes de TI — ransomware, falha de disco, exclusão acidental ou falha de data center. Estudos da indústria mostram que 60% das empresas que perdem dados críticos encerram atividades dentro de 6 meses. O backup bem feito não é apenas cópia de arquivos: é uma política com objetivos claros de recuperação.\n\nDois conceitos definem uma política de backup robusta: o RPO (Recovery Point Objective) — quanto de dado pode ser perdido, medido em tempo — e o RTO (Recovery Time Objective) — em quanto tempo o sistema precisa estar operacional após a falha. Uma empresa que não pode perder mais de 4 horas de dados e precisa estar online em 2 horas tem requisitos completamente diferentes de uma que aceita perder 1 dia e pode ficar 24h fora.\n\nA PaperMoon conduz todo o processo: levantamento dos dados críticos, definição de RPO e RTO com o gestor, escolha da ferramenta de backup adequada ao ambiente (Veeam para ambientes VMware/Windows, BorgBackup ou Restic para Linux, Proxmox Backup Server para VMs Proxmox), implementação da regra 3-2-1 (3 cópias, 2 mídias diferentes, 1 offsite) e testes de restauração documentados. O Plano de Recuperação de Desastres (DRP) é entregue ao final.",
    differentials: [
      "Definição de RPO e RTO antes de qualquer configuração — backup alinhado ao risco real do negócio",
      "Regra 3-2-1 implementada: cópia local + cópia offsite (nuvem ou site remoto)",
      "Testes de restore documentados: backup que não é testado não existe",
      "DRP (Plano de Recuperação de Desastres) entregue como documento operacional ao fim do projeto",
      "Monitoramento de jobs com alerta imediato por e-mail quando um backup falha",
    ],
    comingSoon: false,
    icon: Archive,
    ...SERVICE_TONES.success,
    heroImage: null,
    heroImageAlt: "Backup corporativo — servidores de armazenamento e replicação",
    metaTitle: "Backup corporativo e política DRP — PaperMoon",
    metaDescription:
      "A PaperMoon implanta backup corporativo completo: RPO/RTO, Veeam, BorgBackup, Restic, testes de restore e documentação de recuperação de desastres.",
    papermoonDoes: [
      "Levanta os dados críticos e define RPO/RTO junto com o cliente",
      "Seleciona e configura a ferramenta de backup adequada ao ambiente",
      "Configura jobs de backup com retenção, rotação e criptografia",
      "Implementa backup 3-2-1: 3 cópias, 2 mídias, 1 offsite",
      "Realiza e documenta testes de restore para validação",
      "Entrega a documentação do plano de recuperação de desastres (DRP)",
    ],
    clientDoes: [
      "Definir quais dados e sistemas são críticos para o negócio",
      "Fornecer servidor de destino para backup local (ou contratar cloud)",
      "Validar os testes de restore apresentados pela PaperMoon",
      "Manter o ambiente de backup ativo e monitorado após a implantação",
    ],
    steps: [
      {
        num: "01",
        title: "Levantamento e política",
        description:
          "Identificamos todos os dados críticos do cliente — arquivos, banco de dados, VMs, e-mail —, definimos RPO (quanto de dado pode ser perdido) e RTO (em quanto tempo o sistema deve voltar), e projetamos a arquitetura de backup.",
      },
      {
        num: "02",
        title: "Implantação e automação",
        description:
          "Configuramos os jobs de backup com criptografia, compressão e retenção. Implementamos a regra 3-2-1: cópia local no servidor NAS, cópia offsite em nuvem ou localização remota. Monitoramento e alertas por e-mail incluídos.",
      },
      {
        num: "03",
        title: "Teste de restore e DRP",
        description:
          "Realizamos testes de restauração de cada tipo de dado para validar a integridade dos backups. Documentamos o procedimento passo a passo no Plano de Recuperação de Desastres — para que qualquer técnico consiga executar sem depender da PaperMoon.",
      },
    ],
    featureGroups: [
      {
        title: "Cobertura de dados",
        items: [
          "Arquivos e pastas compartilhadas (servidores Windows e Linux)",
          "Bancos de dados (PostgreSQL, MySQL, SQL Server, MongoDB)",
          "Máquinas virtuais (Proxmox, VMware, Hyper-V)",
          "E-mail (Exchange, Zimbra, Google Workspace)",
          "Configurações de rede e firewalls",
        ],
      },
      {
        title: "Ferramentas e destinos",
        items: [
          "BorgBackup e Restic — backup incremental deduplidado",
          "Veeam Community Edition — backup de VMs",
          "Bacula — backup corporativo multi-cliente",
          "Destino local: NAS TrueNAS ou servidor dedicado",
          "Destino offsite: S3 (AWS, Cloudflare R2, Backblaze B2)",
        ],
      },
      {
        title: "Confiabilidade e compliance",
        items: [
          "Criptografia AES-256 em trânsito e em repouso",
          "Retenção configurável: diário, semanal, mensal, anual",
          "Alertas de falha de job por e-mail e/ou Telegram",
          "Testes de restore periódicos documentados",
          "DRP com RTO e RPO definidos e validados",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença entre backup local e offsite?",
        a: "Backup local (NAS na empresa) permite restore rápido mas não protege contra incêndio, roubo ou desastre físico. Backup offsite (nuvem ou localização remota) protege contra esses cenários mas o restore é mais lento. A regra 3-2-1 combina os dois para máxima proteção.",
      },
      {
        q: "Com que frequência os backups são feitos?",
        a: "Depende do RPO definido. Dados críticos como banco de dados podem ser backupeados a cada hora. Arquivos podem ser diários. A política é definida em conjunto com o cliente no levantamento inicial.",
      },
      {
        q: "Como sei que o backup está funcionando?",
        a: "Configuramos alertas por e-mail para sucesso e falha de cada job. Além disso, realizamos testes de restore periódicos (mensais ou trimestrais) e documentamos o resultado — assim você tem evidência de que os backups são restauráveis.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "A implantação é cobrada como projeto único — levantamento, configuração, testes e documentação DRP. Não há mensalidade da PaperMoon. Os custos de armazenamento offsite (nuvem) são pagos diretamente ao provedor de storage.",
      },
      {
        q: "O que é a regra 3-2-1 e por que ela é importante?",
        a: "A regra 3-2-1 é o padrão-ouro de backup: 3 cópias dos dados, em 2 tipos de mídia diferentes, com 1 cópia offsite. Exemplo: dados no servidor principal (1), backup no NAS local (2), backup na nuvem como Backblaze B2 (3). Essa estratégia garante que nenhum evento isolado — falha de disco, incêndio, ransomware — consiga destruir todas as cópias ao mesmo tempo. A PaperMoon implementa essa regra como padrão em todos os projetos de backup.",
      },
    ],
    prerequisites: [
      "Acesso SSH aos servidores e sistemas de origem do backup",
      "Destino de backup definido: servidor local, NAS, nuvem (S3, Backblaze, Wasabi) ou misto",
      "Volume de dados estimado para dimensionamento do storage de destino",
      "Janela de execução preferida para os jobs de backup (horário de menor uso)",
    ],
  },

  /* ── RustDesk ──────────────────────────────────────────────────── */
  {
    slug: "rustdesk",
    name: "RustDesk",
    tagline: "Acesso remoto seguro e auto-hospedado, sem custo por dispositivo.",
    description:
      "Alternativa open-source ao TeamViewer e AnyDesk, rodando 100% no seu servidor. Acesso remoto criptografado ponta a ponta para Windows, macOS, Linux, iOS e Android — sem mensalidade, sem limite de dispositivos.",
    about:
      "O RustDesk foi criado em 2021 por um desenvolvedor de Hong Kong que publicou o projeto como open-source no GitHub como resposta direta aos preços crescentes do TeamViewer e AnyDesk — ferramentas que chegam a cobrar R$ 200–500 por mês por técnico com um número limitado de dispositivos gerenciados. Escrito em Rust (linguagem de programação conhecida por performance e segurança de memória), o RustDesk se tornou rapidamente um dos projetos open-source de crescimento mais rápido na área de suporte remoto.\n\nA diferença fundamental do RustDesk é a arquitetura self-hosted: toda a comunicação entre o técnico e o dispositivo controlado passa pelo servidor relay instalado na VPS do cliente — não pelos servidores da empresa do software. Isso significa que o tráfego de acesso remoto nunca toca infraestrutura de terceiros, eliminando um vetor de espionagem corporativa e atendendo requisitos de compliance de setores como financeiro, saúde e jurídico.\n\nA PaperMoon instala o servidor relay (hbbs + hbbr) na VPS do cliente, configura o DNS para o endereço do relay, e distribui o cliente RustDesk pré-configurado para os dispositivos da empresa. O técnico de suporte acessa qualquer dispositivo autorizado com a mesma experiência do TeamViewer — sem login externo, sem dependência de conta SaaS.",
    differentials: [
      "Servidor relay próprio na sua VPS: tráfego de acesso remoto nunca sai da sua infraestrutura",
      "Zero custo por dispositivo ou por técnico — sem mensalidade independente do tamanho da equipe",
      "Clientes para Windows, macOS, Linux, Android e iOS em uma única solução",
      "Criptografia end-to-end: comunicação protegida mesmo com relay próprio",
      "Alternativa direta ao TeamViewer (R$200+/mês/técnico) sem abrir mão da experiência de uso",
    ],
    comingSoon: false,
    icon: Monitor,
    ...SERVICE_TONES.warning,
    heroImage: null,
    heroImageAlt: "RustDesk — painel de controle self-hosted para acesso remoto",
    metaTitle: "RustDesk Self-Hosted — Acesso remoto open-source — PaperMoon",
    metaDescription:
      "A PaperMoon instala o RustDesk Server na sua VPS: acesso remoto seguro, criptografado e sem custo por dispositivo. Alternativa open-source ao TeamViewer.",
    papermoonDoes: [
      "Instalação dos dois componentes de servidor (hbbs + hbbr) via Docker na sua VPS",
      "Configuração de SSL/TLS, firewall e portas dedicadas ao RustDesk",
      "Geração e distribuição de chaves criptográficas da sua organização",
      "Build de cliente customizado com logo e nome da empresa (opcional)",
      "Configuração de acesso não supervisionado para servidores e estações fixas",
      "Monitoramento de disponibilidade dos servidores RustDesk via Zabbix",
    ],
    clientDoes: [
      "Instalar o cliente RustDesk nos dispositivos que deseja acessar (Windows, macOS, Linux)",
      "Configurar senha de acesso não supervisionado nas máquinas permanentes",
      "Gerenciar quais colaboradores têm permissão de acesso a cada dispositivo",
      "Instalar o app RustDesk Mobile (iOS/Android) para acesso pelo celular",
    ],
    steps: [
      {
        num: "01",
        title: "Servidor RustDesk na sua VPS",
        description:
          "Implantamos os dois componentes do servidor RustDesk — hbbs (registro de IDs) e hbbr (relay de tráfego) — via Docker na sua VPS, com SSL e firewall configurados.",
      },
      {
        num: "02",
        title: "Clientes configurados e distribuídos",
        description:
          "Fornecemos o cliente pré-configurado com o endereço do seu servidor e a chave criptográfica. Opcionalmente, compilamos um cliente com a identidade visual da empresa para distribuição interna.",
      },
      {
        num: "03",
        title: "Treinamento do time de TI",
        description:
          "Treinamos o time de suporte para usar o RustDesk: acesso supervisionado e não supervisionado, transferência de arquivos, chat integrado e boas práticas de segurança.",
      },
    ],
    featureGroups: [
      {
        title: "Conectividade",
        items: [
          "Conexão P2P direta sempre que possível (menor latência)",
          "Relay automático quando P2P não é viável (firewalls, CGNAT)",
          "Suporte a múltiplos monitores com troca rápida",
          "Resolução adaptativa conforme a largura de banda disponível",
          "Acesso não supervisionado por senha permanente por dispositivo",
        ],
      },
      {
        title: "Segurança",
        items: [
          "Criptografia ponta a ponta — Curve25519 + AES-256-GCM",
          "Chave privada gerada e armazenada só na sua VPS",
          "Sem dados de conexão em servidores de terceiros",
          "Autenticação por senha por sessão ou permanente por dispositivo",
          "Compatível com políticas LGPD e ISO 27001",
        ],
      },
      {
        title: "Compatibilidade",
        items: [
          "Windows 7+ (32 e 64 bits)",
          "macOS 10.14+ (Intel e Apple Silicon)",
          "Linux (Ubuntu, Debian, CentOS, Fedora, openSUSE)",
          "iOS — visualização de tela",
          "Android — controle completo",
        ],
      },
      {
        title: "Recursos avançados",
        items: [
          "Transferência de arquivos bidirecional via drag-and-drop",
          "Chat de texto integrado à sessão",
          "Área de transferência (clipboard) sincronizada entre máquinas",
          "Gravação de sessão local para auditoria",
          "API REST para integração com GLPI e sistemas de ITSM",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença para TeamViewer ou AnyDesk?",
        a: "TeamViewer e AnyDesk são serviços proprietários cobrados por usuário ou dispositivo, com dados de conexão passando pelos servidores deles. O RustDesk self-hosted é open-source, sem custo por dispositivo e com toda a infraestrutura na sua VPS — nenhum dado de sessão sai da sua rede.",
      },
      {
        q: "É possível personalizar o cliente com a marca da empresa?",
        a: "Sim. O RustDesk permite compilar um cliente customizado com nome, logo e servidor pré-configurado. A PaperMoon realiza o build e distribui os instaladores para Windows, macOS e Linux com a identidade visual da sua empresa.",
      },
      {
        q: "Quantos dispositivos e usuários posso ter?",
        a: "Não há limite de dispositivos ou usuários no RustDesk self-hosted. Uma VPS com 2 vCPU e 2 GB RAM comporta centenas de sessões simultâneas. O único limite é a capacidade do servidor relay que você escolher.",
      },
      {
        q: "Como funciona o acesso não supervisionado?",
        a: "Cada máquina pode ter uma senha permanente configurada. Com ela, o técnico acessa o equipamento mesmo sem ninguém presente — útil para servidores e máquinas de produção. A senha pode ser rotacionada a qualquer momento.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "A implantação é cobrada como projeto único — instalação, configuração, SSL, chaves criptográficas, treinamento e documentação. Não há mensalidade da PaperMoon. Você paga apenas a VPS onde o servidor roda.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 1 vCPU, 1 GB RAM, 20 GB SSD) para o servidor relay",
      "Acesso SSH à VPS com usuário root ou sudo",
      "Porta 21115–21119 liberadas no firewall da VPS",
      "Computadores clientes com Windows, Linux ou macOS para instalar o RustDesk Client",
    ],
  },
  {
    slug: "windows-server",
    name: "Windows Server",
    tagline: "Active Directory, servidor de arquivos e políticas de grupo para ambientes Microsoft corporativos.",
    description:
      "Implantamos e gerenciamos a infraestrutura Windows Server da sua empresa: Active Directory com estrutura de UOs e GPOs, servidor de arquivos com permissões NTFS granulares, DNS, DHCP e integração com Microsoft 365 / Entra ID.",
    about:
      "O Windows Server é a plataforma de servidor da Microsoft com mais de 40 anos de história corporativa. Para ambientes que dependem de Active Directory, Group Policies, servidores de arquivos com permissões NTFS, SQL Server, Exchange ou aplicações LOB (Line of Business) legadas, o Windows Server é a única escolha tecnicamente viável — não há equivalente open-source para o conjunto completo de serviços de diretório do Active Directory com a mesma maturidade e interoperabilidade.\n\nUm ambiente Windows Server bem estruturado começa pelo Active Directory: a hierarquia de Unidades Organizacionais (UOs) define como os usuários, computadores e grupos são organizados, e as GPOs (Group Policies) controlam centenas de comportamentos — desde política de senha e bloqueio de tela até instalação de software e acesso a unidades de rede. Sem uma estrutura de OU bem planejada, a gestão do AD se torna impossível de manter conforme a empresa cresce.\n\nA PaperMoon projeta a estrutura do Active Directory conforme o organograma da empresa, cria as UOs e GPOs alinhadas à política de segurança do cliente, configura o servidor de arquivos com compartilhamentos e permissões NTFS granulares, e integra com o Microsoft 365 via Entra ID Connect para que os usuários usem a mesma credencial nos sistemas locais e na nuvem Microsoft.",
    differentials: [
      "Estrutura de OU e GPO projetada conforme o organograma real — não uma estrutura genérica",
      "Integração com Microsoft 365 via Entra ID Connect: credencial única para local e nuvem",
      "Servidor de arquivos com permissões NTFS granulares por pasta e grupo de segurança",
      "WSUS configurado para controle de updates corporativos — sem atualizações surpresa",
      "Hyper-V aproveitado como hypervisor nativo sem custo adicional de licença",
    ],
    comingSoon: false,
    icon: Users,
    ...SERVICE_TONES.info,
    heroImage: null,
    heroImageAlt: "Windows Server — Active Directory e servidor de arquivos corporativo",
    metaTitle: "Windows Server — Active Directory e Servidor de Arquivos — PaperMoon",
    metaDescription:
      "A PaperMoon implanta e gerencia Windows Server na sua empresa: Active Directory, GPOs, servidor de arquivos NTFS e integração com Microsoft 365. Infraestrutura Microsoft configurada por especialistas.",
    papermoonDoes: [
      "Instalação e configuração do Windows Server 2019/2022 (Standard ou Datacenter)",
      "Promoção do Domain Controller e configuração do Active Directory Domain Services (AD DS)",
      "Estrutura de Unidades Organizacionais (UOs), grupos de segurança e delegação de administração",
      "Políticas de Grupo (GPOs): senhas, mapeamento de drives, restrições de software e segurança",
      "Servidor de arquivos com compartilhamentos NTFS, permissões por grupo, quotas e Shadow Copies",
      "Integração com Microsoft 365 / Entra ID via Microsoft Entra Connect (AD Sync)",
      "Configuração de DNS interno, DHCP com reservas e WSUS para patches centralizados",
      "Backup do AD (System State) e dos dados com agendamento automático",
      "Monitoramento de disponibilidade do servidor e dos serviços via Zabbix",
    ],
    clientDoes: [
      "Fornecer a licença do Windows Server (SPLA via CSP ou licença perpétua)",
      "Definir a política de grupos de segurança e permissões de acesso por departamento",
      "Aprovar alterações de GPO antes da aplicação em produção",
      "Gerenciar a criação e desativação de contas de usuário (ou delegar à PaperMoon por contrato)",
    ],
    steps: [
      {
        num: "01",
        title: "Active Directory e domínio",
        description:
          "Instalamos o Windows Server, promovemos o Domain Controller, definimos a estrutura de UOs e importamos ou criamos todos os usuários e grupos da organização. DNS e DHCP são configurados para o domínio.",
      },
      {
        num: "02",
        title: "Servidor de arquivos e permissões",
        description:
          "Criamos os shares de rede com permissões NTFS granulares por grupo de segurança, quotas por usuário, Shadow Copies para recuperação de versões anteriores e mapeamento automático via GPO nas estações do domínio.",
      },
      {
        num: "03",
        title: "GPOs, segurança e integração M365",
        description:
          "Aplicamos políticas de grupo corporativas: bloqueio de mídia removível, políticas de senha, padronização de estações e restrições de software. Integramos ao Microsoft 365 via Entra Connect para SSO unificado.",
      },
    ],
    featureGroups: [
      {
        title: "Active Directory",
        items: [
          "Domínio Windows com estrutura de UOs por departamento",
          "Grupos de segurança para controle de acesso a recursos",
          "Delegação de administração por área sem dar acesso de Domain Admin",
          "Integração com Microsoft 365 / Entra ID (Single Sign-On unificado)",
          "Fine-Grained Password Policies — políticas de senha por grupo",
        ],
      },
      {
        title: "Servidor de Arquivos",
        items: [
          "Compartilhamentos NTFS com permissões por grupo de segurança do AD",
          "Quotas de disco por usuário ou pasta compartilhada",
          "Shadow Copies automáticas — recuperação de versões anteriores em segundos",
          "DFS (Distributed File System) para namespace unificado entre servidores",
          "Auditoria de acesso a arquivos — quem abriu, modificou ou excluiu",
        ],
      },
      {
        title: "Gerenciamento Centralizado",
        items: [
          "GPOs para padronizar todas as estações e servidores do domínio",
          "WSUS — patches e atualizações Windows aprovadas e distribuídas centralmente",
          "DHCP com reservas por MAC e escopos segmentados por VLAN",
          "DNS interno com zones de pesquisa direta e reversa",
        ],
      },
      {
        title: "Segurança",
        items: [
          "Políticas de senha: complexidade, validade e histórico por GPO",
          "BitLocker via GPO para criptografia de disco em laptops",
          "Account Lockout automático após tentativas falhas",
          "MFA com Microsoft Entra ID para acesso a aplicações cloud",
          "Monitoramento de eventos de segurança via Zabbix",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual versão do Windows Server é implantada?",
        a: "Trabalhamos com Windows Server 2019 e 2022 (Standard ou Datacenter, conforme a necessidade de VMs). A versão recomendada para novos projetos é o Windows Server 2022, com suporte estendido até 2031.",
      },
      {
        q: "Preciso comprar a licença? Como funciona?",
        a: "Sim, a licença do Windows Server é responsabilidade do cliente. As opções mais comuns são: licença perpétua (OEM/Retail), SPLA via provedores CSP (pagamento mensal por servidor) ou Microsoft 365 Business Premium para ambientes híbridos. A PaperMoon orienta sobre a melhor opção para o seu caso.",
      },
      {
        q: "É possível integrar com o Microsoft 365 (Office 365)?",
        a: "Sim. A PaperMoon configura o Microsoft Entra Connect (antigo Azure AD Connect) para sincronizar usuários e senhas entre o Active Directory local e o Entra ID. Com isso, o colaborador usa a mesma credencial para logar na estação e acessar Teams, Outlook e SharePoint.",
      },
      {
        q: "O que acontece se o servidor cair? O AD deixa de funcionar?",
        a: "Recomendamos dois Domain Controllers para alta disponibilidade. Com dois DCs, a autenticação no domínio continua funcionando mesmo com um servidor fora do ar. Também configuramos backup automatizado do System State para restauração rápida.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "O projeto de implantação (instalação, AD, GPOs, servidor de arquivos, treinamento e documentação) é cobrado como projeto único. Suporte contínuo e gerenciamento mensal são contratados separadamente conforme a necessidade.",
      },
    ],
    prerequisites: [
      "Licença do Windows Server (2019, 2022 ou superior) e CALs necessárias",
      "Hardware ou VM dedicada compatível (mínimo 4 vCPU, 8 GB RAM, 80 GB SSD para o SO)",
      "Acesso ao console da VM ou KVM-over-IP para instalação",
      "Definição do papel do servidor: AD DS, File Server, IIS, RDS ou combinação",
    ],
  },
  {
    slug: "samba",
    name: "Samba — Servidor de Arquivos",
    tagline: "Compartilhamento de arquivos em Linux, compatível nativamente com Windows, macOS e Linux.",
    description:
      "Implantamos o Samba no Linux para fornecer servidor de arquivos de alta performance via protocolo SMB/CIFS. Acesso nativo de máquinas Windows sem cliente adicional, controle granular de permissões, auditoria de acessos e quotas por usuário — sem custo de licença de sistema operacional.",
    about:
      "O Samba existe desde 1992, criado pelo australiano Andrew Tridgell como implementação reverse-engineered do protocolo SMB da Microsoft para Linux. Hoje é mantido como projeto open-source pela Samba Team e é a solução mais amplamente adotada para ambientes de rede heterogêneos onde máquinas Windows, macOS e Linux precisam compartilhar arquivos e impressoras pelo mesmo protocolo.\n\nA proposta do Samba é clara: transformar qualquer servidor Linux em um file server compatível nativo com o Windows Explorer — sem instalar nenhum software adicional nas estações. Máquinas Windows mapeiam compartilhamentos Samba exatamente como fazem com Windows Server, com a mesma experiência de usuário, mas com o servidor rodando em Ubuntu Server em hardware que custa a metade do equivalente Windows.\n\nA PaperMoon instala o Samba no servidor Linux do cliente, configura os compartilhamentos por departamento com controle de acesso baseado em grupos, habilita a auditoria de acessos (quem abriu, modificou ou deletou qual arquivo e quando), define quotas de disco por usuário e integra com o Active Directory existente via Winbind para que as credenciais de rede do Windows funcionem transparentemente no Samba.",
    differentials: [
      "Sem custo de licença de Windows Server — o servidor de arquivos roda em Ubuntu Linux",
      "Integração com Active Directory via Winbind: mesma credencial do Windows para o file server",
      "Auditoria de acessos por arquivo: registra quem abriu, modificou e deletou cada documento",
      "Quotas de disco configuráveis por usuário ou grupo — controle de uso de armazenamento",
      "Performance superior ao Windows Server em hardware equivalente para workloads de arquivos",
    ],
    comingSoon: false,
    icon: FolderOpen,
    ...SERVICE_TONES.neutral,
    heroImage: null,
    heroImageAlt: "Samba — servidor de arquivos Linux com compartilhamento SMB/CIFS",
    metaTitle: "Samba Servidor de Arquivos Linux — Compartilhamento SMB — PaperMoon",
    metaDescription:
      "A PaperMoon instala o Samba no Linux para compartilhamento de arquivos SMB/CIFS: permissões POSIX + ACL, autenticação AD, quotas e auditoria. Alternativa open-source ao Windows File Server.",
    papermoonDoes: [
      "Instalação do Samba em Linux (Ubuntu Server / Debian / RHEL) na sua VPS ou servidor físico",
      "Configuração de compartilhamentos (shares) por departamento, projeto ou perfil de acesso",
      "Controle de permissões POSIX + ACLs estendidas por usuário e grupo",
      "Autenticação local com usuários Samba ou integrada ao Active Directory Windows (domain member)",
      "Quotas de disco por usuário ou share com alertas automáticos de capacidade",
      "Auditoria de acessos: log de quem abriu, modificou e excluiu arquivos",
      "Criptografia de tráfego SMB3 para segurança em redes sem fio e WAN",
      "Backup dos dados via Rsync ou integração com TrueNAS/Proxmox Backup Server",
      "Monitoramento de disponibilidade e capacidade de disco via Zabbix",
    ],
    clientDoes: [
      "Mapear os drives de rede nas estações Windows (ou via GPO se tiver Active Directory)",
      "Definir estrutura de pastas e política de acesso por departamento",
      "Gerenciar usuários Samba (ou integrar ao AD existente para credenciais unificadas)",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação e estrutura de shares",
        description:
          "Instalamos o Samba no servidor Linux, criamos os compartilhamentos por departamento com permissões POSIX + ACL e integramos ao DNS da rede para que as máquinas localizem os shares pelo nome.",
      },
      {
        num: "02",
        title: "Autenticação e permissões",
        description:
          "Configuramos autenticação local com usuários Samba ou integramos ao Active Directory Windows existente (Samba como domain member) — as credenciais de domínio passam a funcionar diretamente nos shares Linux.",
      },
      {
        num: "03",
        title: "Quotas, auditoria e backup",
        description:
          "Ativamos quotas de disco por usuário, log de auditoria de acessos e rotina de backup incremental dos dados compartilhados. Monitoramento de espaço e disponibilidade via Zabbix com alertas configuráveis.",
      },
    ],
    featureGroups: [
      {
        title: "Compartilhamento",
        items: [
          "Protocolo SMB/CIFS — acesso nativo do Windows sem instalar cliente adicional",
          "Compatível com macOS Finder (AFP via SMB) e Linux via CIFS-utils",
          "Múltiplos shares com configuração independente de permissões e quotas",
          "DFS (Distributed File System) para namespace unificado entre múltiplos servidores",
          "Suporte a links simbólicos e atributos estendidos de arquivo",
        ],
      },
      {
        title: "Autenticação",
        items: [
          "Usuários locais Samba com senha independente",
          "Integração como domain member de Active Directory Windows",
          "Suporte a LDAP para autenticação centralizada",
          "Winbind para mapeamento de usuários AD para UIDs Linux",
          "Suporte a grupos aninhados do Active Directory nas permissões de share",
        ],
      },
      {
        title: "Segurança e Auditoria",
        items: [
          "Permissões POSIX + ACLs estendidas por usuário e grupo",
          "Criptografia de tráfego SMB3 (obrigatória ou opcional por share)",
          "Log de auditoria: abertura, escrita, exclusão e renomeação de arquivos",
          "Bloqueio de acesso por IP ou sub-rede por share",
          "Integração com fail2ban para proteção contra força bruta",
        ],
      },
      {
        title: "Performance e Disponibilidade",
        items: [
          "Rsync para replicação assíncrona entre servidores",
          "Backup incremental agendado com retenção configurável",
          "Cache de metadados para melhor performance em redes de alta latência",
          "Monitoramento de IOPS, espaço e disponibilidade via Zabbix",
          "Notificações automáticas quando o disco ultrapassa 80% de uso",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença entre Samba e Windows Server para arquivos?",
        a: "Funcionalmente equivalentes para a maioria das empresas: ambos falam SMB/CIFS e integram ao Active Directory. A diferença principal é custo e plataforma — o Samba roda em Linux (sem licença de SO) e é open-source, enquanto o Windows File Server exige licença do Windows Server. Para empresas sem AD existente e sem necessidade de GPOs, o Samba é a escolha mais econômica.",
      },
      {
        q: "Máquinas Windows acessam o Samba sem instalar nada?",
        a: "Sim. O Samba fala SMB/CIFS, o mesmo protocolo nativo do Windows. O usuário simplesmente mapeia o drive de rede (\\\\servidor\\share) ou acessa via explorador de arquivos — sem nenhum software adicional na estação.",
      },
      {
        q: "É possível integrar ao Active Directory Windows existente?",
        a: "Sim. O Samba pode operar como domain member do AD Windows. Com isso, os usuários usam as mesmas credenciais de domínio para acessar os shares Linux — sem criar contas duplicadas. A sincronização de grupos de segurança do AD nas permissões do Samba também é suportada.",
      },
      {
        q: "Qual sistema operacional Linux é usado?",
        a: "Recomendamos Ubuntu Server LTS (22.04 ou 24.04) para novos projetos, por ter suporte de longo prazo e boa integração com o Samba. Também suportamos Debian, Rocky Linux e RHEL conforme preferência do cliente.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "O projeto de implantação (instalação, configuração de shares, permissões, autenticação, quotas, backup e treinamento) é cobrado como projeto único. Não há custo de licença de SO. O cliente paga apenas o servidor (VPS ou físico) onde o Samba roda.",
      },
    ],
    prerequisites: [
      "Servidor Linux com Ubuntu 22.04 LTS (mínimo 1 vCPU, 2 GB RAM, storage conforme volume de dados)",
      "Acesso SSH ao servidor com usuário root ou sudo",
      "Lista de compartilhamentos (shares), usuários e permissões desejados",
      "Integração com Active Directory existente se aplicável (opcional)",
    ],
  },

  /* ── Plone ─────────────────────────────────────────────────────── */
  {
    slug: "plone",
    name: "Plone CMS",
    tagline: "Portal corporativo e gestão de conteúdo enterprise com total controle dos seus dados.",
    description:
      "Implantamos o Plone na sua infraestrutura: intranet corporativa, portal de documentos, base de conhecimento ou site institucional com controle de acesso granular, versionamento de conteúdo e integração com LDAP/Active Directory.",
    about:
      "O Plone é um dos sistemas de gerenciamento de conteúdo mais antigos e seguros do mercado, desenvolvido desde 2001 sobre o framework Zope/Python. Seu histórico de segurança é notável: não há vulnerabilidades CVE críticas registradas nos últimos anos, o que levou à sua adoção por organizações governamentais, militares e acadêmicas nos Estados Unidos e na Europa como plataforma de intranet e gestão documental.\n\nO que diferencia o Plone dos CMSs mais populares como WordPress ou Drupal é sua arquitetura voltada para controle rigoroso de conteúdo: fluxo de publicação configurável (rascunho → revisão → aprovação → publicação), versionamento automático de todas as edições com comparação de versões, controle de acesso por conteúdo individual (não apenas por pasta) e suporte nativo a fluxos de trabalho editoriais complexos — ideal para intranets corporativas onde diferentes equipes têm permissões diferentes sobre diferentes seções.\n\nA PaperMoon instala o Plone com a versão mais recente da linha 6.x, configura o tema institucional da empresa, define os tipos de conteúdo necessários (documentos, notícias, procedimentos, FAQs), configura os fluxos de publicação e treina as equipes de conteúdo e administração.",
    differentials: [
      "Histórico de segurança excepcional: adotado por governos e órgãos militares europeus e americanos",
      "Fluxo de publicação configurável: nenhum conteúdo publicado sem aprovação do responsável",
      "Versionamento automático de todo conteúdo com comparação entre versões",
      "Controle de acesso por conteúdo individual — não apenas por pasta ou categoria",
      "Integração com LDAP/Active Directory para login corporativo unificado",
    ],
    comingSoon: false,
    icon: Globe,
    ...SERVICE_TONES.info,
    heroImage: null,
    heroImageAlt: "Plone CMS — portal corporativo e gestão de conteúdo enterprise",
    metaTitle: "Plone CMS Self-Hosted — Intranet e Portal Corporativo — PaperMoon",
    metaDescription:
      "A PaperMoon instala e configura o Plone na sua infraestrutura: portal corporativo, intranet, gestão de documentos com controle de acesso por workflow e integração com Active Directory.",
    papermoonDoes: [
      "Instalação do Plone 6 em servidor Linux (Ubuntu/Debian) via Docker ou buildout",
      "Configuração de portal corporativo com temas responsivos e identidade visual da empresa",
      "Estrutura de tipos de conteúdo: documentos, notícias, eventos, base de conhecimento",
      "Controle de acesso por papel (roles): leitor, redator, editor, gerente e administrador",
      "Workflow de publicação configurável: rascunho → revisão → publicado",
      "Integração com LDAP / Active Directory para login único",
      "Configuração de SSL, proxy reverso Nginx e backups automáticos",
      "Treinamento da equipe editorial e documentação de operação",
    ],
    clientDoes: [
      "Definir a estrutura de seções e tipos de conteúdo desejados",
      "Fornecer identidade visual (cores, logo, tipografia) para o tema",
      "Definir papéis de usuário e fluxo de aprovação de conteúdo",
      "Gerenciar criação de conteúdo e usuários após a entrega",
    ],
    steps: [
      {
        num: "01",
        title: "Planejamento da arquitetura de conteúdo",
        description:
          "Mapeamos os tipos de conteúdo, hierarquia de seções, papéis de usuário e fluxo de aprovação. Essa etapa define toda a estrutura do portal antes do primeiro deploy.",
      },
      {
        num: "02",
        title: "Instalação e configuração do Plone",
        description:
          "Instalamos o Plone 6 na sua VPS, configuramos o banco de dados ZODB, proxy Nginx com SSL e integrações com LDAP/AD. O ambiente é preparado conforme a arquitetura de conteúdo e as integrações definidas para o projeto.",
      },
      {
        num: "03",
        title: "Tema e identidade visual",
        description:
          "Aplicamos um tema responsivo com as cores e logo da empresa. Configuramos layouts de listagem, páginas internas e componentes reutilizáveis.",
      },
      {
        num: "04",
        title: "Entrega, treinamento e documentação",
        description:
          "Realizamos treinamento presencial ou remoto com a equipe editorial e entregamos documentação operacional cobrindo criação de conteúdo, gestão de usuários e backups.",
      },
    ],
    featureGroups: [
      {
        title: "Gestão de conteúdo",
        items: [
          "Versionamento completo com histórico e rollback",
          "Workflow de publicação customizável por tipo de conteúdo",
          "Agendamento de publicação e expiração automática",
          "Editor rich-text (TinyMCE) e suporte a Markdown",
          "Gerenciamento de mídia: imagens, vídeos e documentos",
        ],
      },
      {
        title: "Controle de acesso",
        items: [
          "Papéis granulares por seção do portal",
          "Integração com LDAP / Active Directory",
          "SSO via plugins (CAS, OAuth2, SAML)",
          "Auditoria de acessos e alterações de conteúdo",
          "Grupos de usuário com permissões herdadas por hierarquia",
        ],
      },
      {
        title: "Infraestrutura e segurança",
        items: [
          "100% self-hosted — dados nunca saem do seu servidor",
          "Backup automático do ZODB e blobs de mídia",
          "Proxy Nginx com HTTPS/TLS (Let's Encrypt ou certificado corporativo)",
          "Cache de páginas com Varnish para alta performance",
          "Suporte a Docker Compose para deploys reproduzíveis",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Plone é adequado para que tipo de empresa?",
        a: "Plone é ideal para empresas e instituições que precisam de portal corporativo, intranet ou gestão documental com controle de acesso rigoroso — especialmente em setores regulados como saúde, educação, governo e jurídico. É a escolha quando privacidade e controle sobre os dados são prioritários.",
      },
      {
        q: "Qual a diferença entre Plone e WordPress?",
        a: "Plone foi projetado para gestão documental e portais corporativos com controle de acesso granular, workflow de publicação e versionamento nativo. WordPress foca em blogs e sites de conteúdo simples. Para intranets com múltiplos papéis de usuário e fluxos de aprovação, Plone é significativamente mais maduro.",
      },
      {
        q: "É possível integrar o Plone ao Active Directory da empresa?",
        a: "Sim. O Plone possui plugins LDAP e SAML para autenticação federada. Com isso, os colaboradores usam as credenciais do domínio Windows para acessar o portal — sem contas duplicadas e com desativação imediata ao sair da empresa.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "O projeto de implantação (instalação, configuração, tema, integrações LDAP, treinamento e documentação) é cobrado como projeto único. Não há licença — Plone é open-source. O cliente paga apenas o servidor onde o Plone roda.",
      },
      {
        q: "O Plone suporta múltiplos idiomas no mesmo portal?",
        a: "Sim. O Plone tem suporte nativo a multilinguismo (via pacote plone.app.multilingual) — cada conteúdo pode ter versões em diferentes idiomas com navegação por idioma do visitante. É especialmente útil para empresas com operações em múltiplos países ou portais com audiência internacional.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 2 vCPU, 4 GB RAM, 40 GB SSD)",
      "Acesso SSH ao servidor com usuário root ou sudo",
      "Domínio configurado com DNS apontando para o servidor",
      "Definição prévia da estrutura de seções e papéis de usuário",
      "Credenciais LDAP/AD se integração de autenticação for desejada (opcional)",
    ],
  },

  /* ── Keycloak ──────────────────────────────────────────────────── */
  {
    slug: "keycloak",
    name: "Keycloak — IAM e SSO",
    tagline: "Login único para todos os sistemas da empresa com segurança enterprise.",
    description:
      "Centralize a autenticação de todas as aplicações da sua empresa em um só lugar. Com Keycloak self-hosted, você tem SSO (Single Sign-On), MFA, controle de sessão, OAuth2/OIDC e SAML 2.0 — sem depender de provedores externos.",
    about:
      "O Keycloak é desenvolvido pela Red Hat desde 2013 e doado à CNCF (Cloud Native Computing Foundation) em 2023, tornando-se o padrão open-source da indústria para gestão de identidade e acesso (IAM). Implementa os protocolos OAuth 2.0, OpenID Connect e SAML 2.0 — os mesmos usados por Google, Microsoft, GitHub e Okta — e é adotado por gigantes como Bosch, Deutsche Telekom e pelo governo da Alemanha para centralizar a autenticação de centenas de sistemas.\n\nO problema que o Keycloak resolve é fundamental: à medida que uma empresa cresce e adopta mais softwares (ERP, CRM, helpdesk, colaboração, monitoramento), cada sistema exige um login separado — diferentes senhas, diferentes políticas, diferentes sessões. O SSO (Single Sign-On) soluciona isso: o usuário autentica uma vez no Keycloak e acessa todos os sistemas integrados sem fazer login novamente. Além do SSO, o Keycloak centraliza o MFA (autenticação multifator), controle de sessão, bloqueio de contas e federação com Active Directory e LDAP.\n\nA PaperMoon instala o Keycloak na VPS do cliente, configura os realms por domínio da empresa, integra com o Active Directory existente via Winbind LDAP, e conecta os sistemas da empresa ao Keycloak usando OIDC ou SAML. A alternativa SaaS mais próxima é o Auth0 ou Okta, que cobram a partir de R$ 200/mês para um número limitado de usuários ativos.",
    differentials: [
      "SSO para todos os sistemas da empresa: um login, todos os acessos — sem múltiplas senhas",
      "Alternativa self-hosted ao Auth0 e Okta — sem mensalidade baseada em usuários ativos",
      "Federação com Active Directory/LDAP: as credenciais corporativas funcionam em todos os sistemas",
      "MFA nativo: TOTP (Google Authenticator), WebAuthn (chave física) e e-mail OTP",
      "Padrões abertos OAuth2, OIDC e SAML: conecta qualquer aplicação moderna sem lock-in",
    ],
    comingSoon: false,
    icon: KeyRound,
    ...SERVICE_TONES.accent,
    heroImage: null,
    heroImageAlt: "Keycloak — Identity and Access Management com SSO e MFA",
    metaTitle: "Keycloak IAM Self-Hosted — SSO, OAuth2 e SAML para Empresas — PaperMoon",
    metaDescription:
      "A PaperMoon instala e configura o Keycloak na sua infra: SSO, MFA, OAuth2, OIDC e SAML 2.0. Login único para todos os sistemas da empresa com total controle de acesso e identidade.",
    papermoonDoes: [
      "Instalação do Keycloak em servidor Linux via Docker Compose ou Helm (Kubernetes)",
      "Configuração de Realm, clientes OAuth2/OIDC e providers SAML 2.0",
      "Integração com LDAP / Active Directory para sincronização de usuários e grupos",
      "Configuração de MFA (TOTP via Google Authenticator / Authy) por papel de usuário",
      "Fluxos de autenticação customizados: login por e-mail, captcha, termos de uso",
      "Integração de aplicações existentes (N8N, Nextcloud, Chatwoot, GLPI, Zabbix)",
      "Configuração de SSL, proxy reverso Nginx e alta disponibilidade",
      "Treinamento da equipe de TI e documentação dos fluxos configurados",
    ],
    clientDoes: [
      "Mapear quais aplicações devem ser integradas ao SSO",
      "Definir políticas de senha e regras de MFA por grupo de usuário",
      "Fornecer credenciais LDAP/AD se integração de diretório for necessária",
      "Gerenciar criação e desativação de usuários e grupos no Keycloak",
    ],
    steps: [
      {
        num: "01",
        title: "Mapeamento de aplicações e identidades",
        description:
          "Levantamos todas as aplicações que precisam de SSO, os grupos de usuário, papéis e políticas de acesso. Esse mapeamento define a estrutura de Realms e clientes no Keycloak.",
      },
      {
        num: "02",
        title: "Instalação e configuração do Keycloak",
        description:
          "Instalamos o Keycloak com banco de dados PostgreSQL, proxy Nginx e SSL. Configuramos o Realm principal, fluxos de autenticação, MFA e integração LDAP/AD.",
      },
      {
        num: "03",
        title: "Integração das aplicações",
        description:
          "Configuramos cada aplicação como cliente OAuth2/OIDC ou SAML. O login passa a ser centralizado — o usuário autentica uma vez e acessa todos os sistemas sem logar novamente.",
      },
      {
        num: "04",
        title: "Treinamento e entrega",
        description:
          "Treinamos a equipe de TI na gestão de usuários, grupos e clientes no console do Keycloak. Entregamos documentação de operação e guia de integração de novas aplicações.",
      },
    ],
    featureGroups: [
      {
        title: "Autenticação e SSO",
        items: [
          "Single Sign-On (SSO) para todos os sistemas integrados",
          "Single Logout — sair de uma app desconecta de todas",
          "Suporte a OAuth2, OpenID Connect (OIDC) e SAML 2.0",
          "Social login: Google, Microsoft, GitHub (configurável)",
          "Impersonation — admin assume sessão de usuário para suporte",
        ],
      },
      {
        title: "Segurança e MFA",
        items: [
          "MFA com TOTP (Google Authenticator, Authy, FreeOTP)",
          "Política de senhas: complexidade, expiração e histórico",
          "Bloqueio de conta após tentativas incorretas",
          "Detecção de força bruta com backoff exponencial",
          "Auditoria de login: quem acessou, quando e de onde",
        ],
      },
      {
        title: "Gestão de identidades",
        items: [
          "Sincronização bidirecional com LDAP / Active Directory",
          "User Federation: usuários gerenciados no AD, autenticados no Keycloak",
          "Grupos e papéis mapeados por regras automáticas do LDAP",
          "Self-service: usuário altera senha e perfil no portal próprio",
          "Convite por e-mail com fluxo de primeiro acesso controlado",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Quais aplicações podem ser integradas ao Keycloak?",
        a: "Qualquer aplicação que suporte OAuth2, OIDC ou SAML pode ser integrada: Nextcloud, GLPI, Zabbix, N8N, Chatwoot, Grafana, Jenkins, Gitea, WordPress, aplicações Django/Node.js/Java e muitas outras. A PaperMoon cuida das configurações de todos os sistemas implantados por nós.",
      },
      {
        q: "Keycloak é difícil de manter?",
        a: "O console web do Keycloak é intuitivo para tarefas do dia a dia — adicionar usuário, resetar senha, bloquear conta. Operações avançadas (novos clientes OIDC, fluxos de autenticação) requerem treinamento, que fazemos parte da entrega. Atualizações são simples via Docker Compose.",
      },
      {
        q: "É possível manter o Active Directory e usar o Keycloak ao mesmo tempo?",
        a: "Sim — é o cenário mais comum. O Keycloak sincroniza usuários do AD via User Federation LDAP. O AD continua sendo a fonte de identidade para estações Windows e o Keycloak centraliza o SSO das aplicações web e cloud.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "Instalação, configuração do Realm, MFA, LDAP e integração das aplicações contratadas são cobrados como projeto único. Keycloak é open-source — sem licença. O cliente paga apenas o servidor onde roda.",
      },
      {
        q: "Keycloak suporta login social (Google, Microsoft, GitHub)?",
        a: "Sim. O Keycloak tem Identity Providers pré-configurados para Google, Microsoft, GitHub, Facebook, Apple e qualquer provedor que suporte OIDC ou SAML. A configuração permite que usuários façam login com conta Google ou Microsoft existente, eliminando a necessidade de criar e gerenciar senha no Keycloak.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 2 vCPU, 4 GB RAM, 30 GB SSD)",
      "Acesso SSH ao servidor com usuário root ou sudo",
      "Domínio configurado com DNS apontando para o servidor",
      "Lista das aplicações a integrar com SSO e seus endpoints de callback",
      "Credenciais LDAP/AD se integração de diretório for necessária (opcional)",
    ],
  },

  /* ── Tailscale ─────────────────────────────────────────────────── */
  {
    slug: "tailscale",
    name: "Tailscale",
    tagline: "Rede privada mesh com acesso remoto seguro, simples e sem abrir portas no firewall.",
    description:
      "Implantamos o Tailscale na sua infraestrutura para conectar notebooks, servidores e filiais em uma rede privada criptografada baseada em WireGuard. Acesso remoto estável, ACLs granulares e administração centralizada sem VPN tradicional complexa.",
    about:
      "O Tailscale foi lançado em 2019 por ex-engenheiros do Google e rapidamente se tornou uma das formas mais práticas de construir redes privadas modernas sem a complexidade de VPNs tradicionais baseadas em IPsec ou OpenVPN. Sua base técnica é o WireGuard, protocolo reconhecido por simplicidade, alta performance e criptografia moderna, mas com uma camada adicional de controle central, descoberta automática de peers, ACLs e autenticação via identidade.\n\nNa prática, o Tailscale resolve um problema muito comum nas empresas: conectar pessoas, notebooks, servidores, filiais e ambientes cloud de forma segura sem depender de redirecionamento de portas, IP fixo, regras complexas de NAT ou túneis frágeis. Em vez de expor serviços na internet, cada dispositivo autorizado entra em uma tailnet privada e só conversa com os recursos permitidos pelas políticas de acesso.\n\nA PaperMoon implanta o Tailscale na operação do cliente com desenho de rede, política de grupos, autenticação com Google ou Microsoft, roteadores de sub-rede para acesso a redes locais e documentação operacional. O resultado é acesso remoto rápido e seguro para equipe de TI, usuários e fornecedores, sem sacrificar visibilidade nem governança.",
    differentials: [
      "Acesso remoto seguro sem expor portas nem depender de IP fixo",
      "Baseado em WireGuard: criptografia moderna, baixa latência e excelente desempenho",
      "ACLs por usuário, grupo, dispositivo e serviço com governança centralizada",
      "Integração com Google Workspace, Microsoft Entra ID e outros provedores SSO",
      "Subnets, exit nodes e compartilhamento controlado para filiais, clouds e parceiros",
    ],
    comingSoon: false,
    icon: Network,
    ...SERVICE_TONES.accent,
    heroImage: null,
    heroImageAlt: "Tailscale — rede privada mesh com WireGuard e controle centralizado",
    metaTitle: "Tailscale Self-Hosted Ready — VPN Mesh Segura para Empresas — PaperMoon",
    metaDescription:
      "A PaperMoon implanta o Tailscale na sua operação: acesso remoto seguro, tailnet privada, ACLs, subnet routers e integração com SSO sem complexidade de VPN tradicional.",
    papermoonDoes: [
      "Desenha a topologia da tailnet conforme filiais, times e ambientes",
      "Instala o agente Tailscale em servidores, notebooks e jump hosts necessários",
      "Configura autenticação com Google, Microsoft ou outro provedor suportado",
      "Define ACLs, tags e grupos de acesso por perfil de usuário e ambiente",
      "Configura subnet routers e exit nodes quando houver redes locais a publicar",
      "Documenta o acesso remoto e treina a equipe para operação diária",
    ],
    clientDoes: [
      "Definir quais usuários, dispositivos e redes devem entrar na tailnet",
      "Aprovar políticas de acesso entre times, fornecedores e ambientes",
      "Fornecer acesso administrativo aos dispositivos ou servidores a integrar",
      "Manter a gestão de usuários no provedor de identidade escolhido",
    ],
    steps: [
      {
        num: "01",
        title: "Mapeamento de acessos",
        description:
          "Levantamos quem precisa acessar o quê: servidores, redes locais, notebooks administrativos, filiais e parceiros. Isso define grupos, tags e políticas de ACL.",
      },
      {
        num: "02",
        title: "Implantação da tailnet",
        description:
          "Instalamos o Tailscale nos dispositivos e servidores necessários, conectamos tudo à tailnet e configuramos autenticação centralizada com o provedor de identidade da empresa.",
      },
      {
        num: "03",
        title: "Políticas e rotas privadas",
        description:
          "Publicamos sub-redes locais via subnet router, configuramos exit nodes quando necessário e aplicamos regras de acesso mínimo para cada time ou fornecedor.",
      },
      {
        num: "04",
        title: "Validação e handoff",
        description:
          "Validamos o acesso remoto em produção, documentamos o fluxo operacional e treinamos a equipe para inclusão de novos dispositivos e troubleshooting básico.",
      },
    ],
    featureGroups: [
      {
        title: "Acesso remoto moderno",
        items: [
          "Rede privada mesh entre notebooks, servidores e clouds",
          "Conexão ponto a ponto sempre que possível para menor latência",
          "Sem abrir portas de RDP, SSH ou painéis na internet",
          "Cliente leve para Windows, macOS, Linux, iOS e Android",
        ],
      },
      {
        title: "Governança e segurança",
        items: [
          "ACLs por usuário, grupo, tag e porta",
          "Integração com SSO corporativo e revogação central de acesso",
          "Logs de acesso e visibilidade dos dispositivos conectados",
          "Aprovação de dispositivos e políticas de menor privilégio",
        ],
      },
      {
        title: "Redes e operação",
        items: [
          "Subnet routers para acessar redes locais sem instalar agente em tudo",
          "Exit nodes para navegação segura por rede controlada",
          "Acesso entre matriz, filial, cloud e home office",
          "Compartilhamento controlado para terceiros e suporte externo",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença entre Tailscale e uma VPN tradicional?",
        a: "VPNs tradicionais costumam exigir concentrador, regras de firewall, NAT, IP fixo e configuração manual de túneis. O Tailscale simplifica isso com WireGuard, descoberta automática de peers, autenticação por identidade e políticas centralizadas. O resultado é implantação muito mais rápida e manutenção mais simples.",
      },
      {
        q: "Preciso abrir portas no roteador ou firewall?",
        a: "Na maioria dos cenários, não. O Tailscale usa NAT traversal para estabelecer conexão direta entre os nós. Quando isso não é possível, ele usa relays DERP sem expor seus serviços diretamente na internet.",
      },
      {
        q: "Consigo acessar uma rede inteira da empresa sem instalar em todos os equipamentos?",
        a: "Sim. Com subnet routers, a PaperMoon publica redes locais inteiras dentro da tailnet. Assim, um notebook autorizado consegue acessar servidores e dispositivos internos mesmo que eles não tenham o agente instalado individualmente.",
      },
      {
        q: "É uma alternativa ao TeamViewer ou AnyDesk?",
        a: "Em muitos cenários, sim. O Tailscale não substitui a ferramenta de controle remoto em si, mas cria a conectividade privada e segura entre os dispositivos. Ele combina muito bem com RDP, SSH, RustDesk e painéis web internos sem precisar expor nada publicamente.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "A implantação, desenho da rede, políticas de ACL, subnet routers e treinamento são cobrados como projeto. Se houver gestão contínua do ambiente, isso pode entrar em contrato mensal de operação. O custo recorrente principal depende do plano escolhido diretamente com o Tailscale, quando aplicável.",
      },
    ],
    prerequisites: [
      "Lista dos usuários, notebooks, servidores e redes que participarão da tailnet",
      "Acesso administrativo aos dispositivos ou servidores a integrar",
      "Provedor de identidade definido (Google, Microsoft ou outro suportado)",
      "Mapeamento de quais redes locais precisam ser publicadas via subnet router",
    ],
  },

  /* ── Twenty CRM ────────────────────────────────────────────────── */
  {
    slug: "twenty-crm",
    name: "Twenty CRM",
    tagline: "CRM open-source e self-hosted — alternativa ao Salesforce com zero custo de licença.",
    description:
      "Implantamos o Twenty CRM na sua infraestrutura: pipeline de vendas, gestão de contatos e empresas, atividades, e-mails e integrações com Slack e calendário — tudo sem mensalidade por usuário e com seus dados no seu servidor.",
    about:
      "O Twenty CRM surgiu em 2023 como uma das iniciativas open-source de crescimento mais rápido no espaço de CRM. Fundado pela empresa francesa Twenty e construído com tecnologias modernas — React no frontend, NestJS no backend, GraphQL para a API — o projeto ultrapassou 10 mil estrelas no GitHub em menos de um ano após o lançamento, o que demonstra o nível de insatisfação com as alternativas existentes.\n\nO problema que o Twenty resolve é o custo proibitivo dos CRMs tradicionais: o Salesforce cobra entre R$ 300 e R$ 1.500 por usuário por mês, o HubSpot tem um plano gratuito muito limitado e planos pagos a partir de R$ 450/mês. Para equipes comerciais de 5 a 20 pessoas, isso representa R$ 30.000 a R$ 180.000 por ano apenas em software de CRM. Com o Twenty auto-hospedado, o custo se limita à VPS e ao serviço de implantação.\n\nA PaperMoon instala o Twenty CRM na VPS do cliente com configuração de produção completa (PostgreSQL, Redis, MinIO para armazenamento de arquivos), configura o pipeline de vendas conforme o processo comercial da empresa, importa a base de contatos existente e realiza treinamento da equipe. A sincronização de e-mail e a integração com Google Calendar ou Outlook Calendar são configuradas no mesmo escopo.",
    differentials: [
      "Zero mensalidade por usuário — economize R$ 30 mil+/ano versus Salesforce ou HubSpot",
      "Interface moderna similar ao Notion: curva de aprendizado mínima para equipes comerciais",
      "Pipeline de vendas configurável conforme o processo real da empresa, não um template genérico",
      "API GraphQL para integrações com ERPs, planilhas e automações via n8n",
      "Seus dados de clientes e oportunidades ficam na sua VPS — nunca em servidor de terceiros",
    ],
    comingSoon: false,
    icon: Building2,
    ...SERVICE_TONES.success,
    heroImage: null,
    heroImageAlt: "Twenty CRM — pipeline de vendas e gestão de clientes self-hosted",
    metaTitle: "Twenty CRM Self-Hosted — Alternativa ao Salesforce — PaperMoon",
    metaDescription:
      "A PaperMoon instala o Twenty CRM na sua infraestrutura: pipeline de vendas, contatos, empresas, atividades e integrações — sem custo por usuário e com total controle dos seus dados de clientes.",
    papermoonDoes: [
      "Instalação do Twenty CRM via Docker Compose em servidor Linux",
      "Configuração de banco de dados PostgreSQL, Redis e storage de arquivos",
      "Customização de objetos: campos adicionais em contatos, empresas e deals",
      "Configuração de pipelines de vendas com etapas personalizadas por equipe",
      "Integração de e-mail corporativo (Gmail/Outlook) para sincronização de conversas",
      "Configuração de SSL, proxy Nginx e backups automáticos",
      "Treinamento da equipe comercial e documentação de operação",
    ],
    clientDoes: [
      "Definir as etapas do pipeline de vendas e campos personalizados por objeto",
      "Configurar credenciais OAuth da conta de e-mail para sincronização",
      "Migrar dados de CRM anterior (planilhas ou exportação do CRM atual)",
      "Gerenciar usuários, permissões e criação de pipelines após entrega",
    ],
    steps: [
      {
        num: "01",
        title: "Mapeamento do processo comercial",
        description:
          "Levantamos as etapas do pipeline, campos customizados de contatos e empresas, e fluxo de atividades da equipe. Esse mapeamento garante que o Twenty reflita o processo real de vendas.",
      },
      {
        num: "02",
        title: "Instalação e configuração",
        description:
          "Instalamos o Twenty via Docker Compose com PostgreSQL, Redis e storage. Configuramos SSL, proxy Nginx e integração de e-mail corporativo para sincronização automática de conversas.",
      },
      {
        num: "03",
        title: "Customização e migração de dados",
        description:
          "Criamos campos personalizados, pipelines e etapas. Importamos os dados do CRM anterior (HubSpot, Salesforce, Pipedrive ou planilhas) via API ou CSV.",
      },
      {
        num: "04",
        title: "Treinamento e entrega",
        description:
          "Treinamos a equipe comercial no uso do Twenty: criação de deals, atividades, filtros e relatórios. Entregamos documentação operacional e guia de administração.",
      },
    ],
    featureGroups: [
      {
        title: "Pipeline e vendas",
        items: [
          "Pipelines configuráveis com etapas personalizadas",
          "Kanban de deals com drag-and-drop entre etapas",
          "Campos customizados por objeto (contato, empresa, deal)",
          "Filtros e visões salvas por equipe ou vendedor",
          "Relatórios de funil: taxa de conversão por etapa",
        ],
      },
      {
        title: "Comunicação e atividades",
        items: [
          "Sincronização bidirecional de e-mails (Gmail e Outlook)",
          "Log de chamadas, reuniões e tarefas por contato",
          "Notas com menção de membros da equipe",
          "Integração com Google Calendar e Outlook Calendar",
          "Timeline completa de interações por empresa e contato",
        ],
      },
      {
        title: "Dados e integração",
        items: [
          "API GraphQL nativa para integração com outros sistemas",
          "Importação via CSV de qualquer CRM ou planilha",
          "Webhooks para automação com N8N ou Zapier",
          "100% self-hosted — dados ficam no seu servidor",
          "Modelo de dados extensível via metadados (sem código)",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Twenty CRM é adequado para que tamanho de empresa?",
        a: "O Twenty é ideal para startups, PMEs e equipes comerciais de até ~200 pessoas. É especialmente atraente para quem está saindo de planilhas ou quer uma alternativa self-hosted ao HubSpot ou Pipedrive sem custo por usuário.",
      },
      {
        q: "É possível migrar dados do HubSpot, Salesforce ou Pipedrive?",
        a: "Sim. O Twenty aceita importação via CSV e tem API GraphQL que permite migração programática. A PaperMoon cuida da migração como parte da entrega — mapeamos campos do CRM atual para os objetos do Twenty e importamos contatos, empresas e histórico de deals.",
      },
      {
        q: "O Twenty CRM tem aplicativo mobile?",
        a: "O Twenty tem interface web responsiva que funciona bem em dispositivos móveis. Um app nativo (iOS/Android) está no roadmap do projeto open-source. Para equipes que precisam de app mobile robusto agora, avalie se a interface web atende ou considere complementar com um app PWA.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "A implantação (instalação, configuração, customização de campos e pipelines, migração de dados e treinamento) é cobrada como projeto único. Não há custo de licença — Twenty é open-source com licença AGPL. O cliente paga apenas o servidor.",
      },
      {
        q: "O Twenty CRM tem integração com e-mail e Google Calendar?",
        a: "Sim. O Twenty integra com Gmail e Google Calendar via OAuth2, e com qualquer servidor de e-mail via IMAP. Mensagens e reuniões com contatos do CRM aparecem automaticamente no histórico do contato ou empresa — sem copiar e colar manualmente. A PaperMoon configura as integrações como parte da entrega.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 2 vCPU, 4 GB RAM, 40 GB SSD)",
      "Acesso SSH ao servidor com usuário root ou sudo",
      "Domínio configurado com DNS apontando para o servidor",
      "Exportação de dados do CRM atual (CSV ou API) se migração for necessária",
      "Credenciais OAuth2 de conta Google ou Microsoft para sincronização de e-mail (opcional)",
    ],
  },

  /* ── Papermark ─────────────────────────────────────────────────── */
  {
    slug: "papermark",
    name: "Papermark",
    tagline: "Compartilhe propostas e documentos com rastreamento total — alternativa ao DocSend.",
    description:
      "Implantamos o Papermark self-hosted: envie documentos com link seguro e saiba exatamente quem abriu, por quanto tempo leu cada página e o que gerou mais interesse — dados que ficam no seu servidor, não em plataformas de terceiros.",
    about:
      "O Papermark surgiu em 2023 como alternativa open-source ao DocSend — ferramenta da Dropbox que cobra entre US$ 15 e US$ 65 por usuário por mês para rastrear o engajamento com propostas e documentos compartilhados. Construído em Next.js com banco PostgreSQL, o projeto foi criado como resposta direta ao aumento de preços do DocSend após sua aquisição pela Dropbox e rapidamente se tornou uma das ferramentas mais adotadas por equipes comerciais que precisam de inteligência sobre suas propostas.\n\nO Papermark resolve um problema específico e valioso: quando você envia uma proposta por e-mail ou PDF, não sabe se o prospect chegou a abrir, quanto tempo passou lendo, quais páginas mais interessaram e se encaminhou para outra pessoa. Com o Papermark, cada documento é compartilhado por um link único com rastreamento: você recebe notificação em tempo real quando o documento é aberto e tem acesso a um dashboard com tempo por página, porcentagem lida e número de visualizações.\n\nA PaperMoon instala o Papermark na VPS do cliente com configuração completa de produção (PostgreSQL, S3-compatible storage para os documentos, SSL), configura as notificações por e-mail e Slack, e orienta a equipe comercial no uso da ferramenta. Documentos confidenciais — propostas financeiras, contratos, memorandos — nunca transitam por servidores de terceiros.",
    differentials: [
      "Self-hosted: propostas e documentos confidenciais ficam na sua infraestrutura, nunca no DocSend/Dropbox",
      "Rastreamento por página: saiba em qual parte da proposta o cliente passou mais tempo",
      "Notificação em tempo real quando o prospect abre o documento — momento ideal para follow-up",
      "Link protegido por senha e com validade configurável — controle total sobre quem acessa",
      "Zero custo de mensalidade versus US$ 15–65/usuário/mês do DocSend",
    ],
    comingSoon: false,
    icon: FileText,
    ...SERVICE_TONES.neutral,
    heroImage: null,
    heroImageAlt: "Papermark — compartilhamento de documentos com analytics self-hosted",
    metaTitle: "Papermark Self-Hosted — Compartilhamento de Documentos com Analytics — PaperMoon",
    metaDescription:
      "A PaperMoon instala o Papermark na sua infraestrutura: compartilhe propostas e documentos com link rastreável, veja quem abriu, tempo por página e taxa de interesse — alternativa self-hosted ao DocSend.",
    papermoonDoes: [
      "Instalação do Papermark via Docker Compose em servidor Linux",
      "Configuração de banco de dados PostgreSQL e storage de documentos (S3 ou local)",
      "Configuração de domínio customizado para os links de compartilhamento",
      "Integração de e-mail transacional para notificações de visualização",
      "Configuração de SSL, proxy Nginx e backups automáticos",
      "Treinamento da equipe comercial e documentação de operação",
    ],
    clientDoes: [
      "Definir domínio customizado para os links de documentos",
      "Fornecer credenciais de e-mail transacional (SendGrid, Resend ou SMTP próprio)",
      "Gerenciar upload de documentos e criação de espaços de trabalho após entrega",
    ],
    steps: [
      {
        num: "01",
        title: "Instalação e configuração",
        description:
          "Instalamos o Papermark via Docker Compose com PostgreSQL e storage. Configuramos SSL, domínio customizado e integração de e-mail para notificações de abertura de documentos.",
      },
      {
        num: "02",
        title: "Configuração de storage de documentos",
        description:
          "Configuramos o armazenamento dos documentos: S3 compatível (MinIO self-hosted ou S3 da AWS) ou volume local — conforme sua preferência de custo e controle.",
      },
      {
        num: "03",
        title: "Treinamento e entrega",
        description:
          "Treinamos a equipe no upload de documentos, criação de links rastreáveis, proteção por senha ou e-mail, e interpretação dos analytics de leitura por página.",
      },
    ],
    featureGroups: [
      {
        title: "Compartilhamento seguro",
        items: [
          "Links únicos por destinatário com rastreamento individual",
          "Proteção por e-mail verificado ou senha por link",
          "Expiração de link por data ou número de visualizações",
          "Desativação imediata de link sem alterar o documento",
          "Suporte a PDF, DOCX, PPTX e arquivos de imagem",
        ],
      },
      {
        title: "Analytics de engajamento",
        items: [
          "Tempo de leitura por página com gráfico de atenção",
          "Total de visualizações por link e por documento",
          "Localização geográfica aproximada do leitor",
          "Notificação em tempo real por e-mail na abertura do link",
          "Histórico completo de sessões por destinatário",
        ],
      },
      {
        title: "Controle e privacidade",
        items: [
          "100% self-hosted — documentos no seu servidor",
          "Sem marca d'água de terceiros nos documentos",
          "Domínio customizado nos links de compartilhamento",
          "Sem limite de documentos ou visualizações (limitado só pelo storage)",
          "Logs de acesso para conformidade e auditoria interna",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença do Papermark para o DocSend?",
        a: "DocSend é um SaaS pago por documento ou usuário com dados armazenados nos servidores deles. O Papermark self-hosted é open-source, sem custo de licença e com documentos no seu servidor — ideal para empresas que compartilham propostas confidenciais e precisam de total controle sobre os dados.",
      },
      {
        q: "Que tipos de arquivo posso compartilhar?",
        a: "PDFs são o formato principal (com analytics por página). O Papermark também suporta DOCX, PPTX e imagens — esses são convertidos para visualização no browser. Para melhores analytics de tempo por página, recomendamos exportar documentos como PDF antes de subir.",
      },
      {
        q: "Os destinatários precisam criar conta para abrir o documento?",
        a: "Não. O destinatário recebe um link e abre o documento diretamente no browser — sem instalar nada nem criar conta. Você pode pedir o e-mail dele antes de liberar o acesso (verificação de e-mail) ou manter o link aberto sem autenticação.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "A implantação (instalação, configuração de storage, domínio customizado, e-mail transacional e treinamento) é cobrada como projeto único. Papermark é open-source — sem licença. O cliente paga apenas o servidor e o storage.",
      },
      {
        q: "Posso criar apresentações no Papermark ou apenas subir documentos?",
        a: "O Papermark trabalha com documentos existentes — você sobe PDFs, DOCX ou PPTX e o sistema gera o link rastreável. Para criar apresentações dentro da plataforma, recomendamos criar o deck no PowerPoint, Keynote ou Canva, exportar como PDF e subir no Papermark para o compartilhamento rastreável.",
      },
    ],
    prerequisites: [
      "VPS com Ubuntu 22.04 LTS (mínimo 1 vCPU, 2 GB RAM, 20 GB SSD + storage para documentos)",
      "Acesso SSH ao servidor com usuário root ou sudo",
      "Domínio configurado com DNS apontando para o servidor",
      "Credenciais de provedor de e-mail transacional (Resend, SendGrid ou SMTP próprio)",
    ],
  },

  /* ── CrowdSec ──────────────────────────────────────────────────── */
  {
    slug: "crowdsec",
    name: "CrowdSec — Segurança Colaborativa",
    tagline: "Proteção automática contra ataques com inteligência de ameaças compartilhada globalmente.",
    description:
      "Implantamos o CrowdSec na sua infraestrutura Linux: detecção de comportamento malicioso em tempo real, bloqueio automático de IPs atacantes e acesso à reputação de IPs de uma rede global de sensores — tudo open-source e self-hosted.",
    about:
      "O CrowdSec foi fundado em 2020 por uma equipe de ex-pesquisadores de segurança franceses e representa uma evolução do paradigma de proteção de servidores: enquanto ferramentas como o Fail2ban analisam os logs localmente e bloqueiam IPs apenas com base no comportamento observado no próprio servidor, o CrowdSec adiciona uma camada de inteligência coletiva — uma rede global de mais de 100 mil servidores que compartilham informações sobre IPs maliciosos em tempo real.\n\nA distinção técnica é importante: o CrowdSec é um IDS/IPS comportamental, não um firewall. O firewall (iptables, UFW, security groups) bloqueia portas e protocolos de forma estática. O CrowdSec analisa os logs das aplicações em tempo real, identifica padrões de comportamento malicioso (tentativas de brute force em SSH, scans de vulnerabilidades em Nginx, exploits em WordPress) e bloqueia o IP atacante dinamicamente antes que o ataque seja concluído — mesmo que o IP nunca tenha atacado especificamente o seu servidor antes, se ele já atacou outros servidores na rede colaborativa, você já está protegido.\n\nA PaperMoon instala o agente CrowdSec em todos os servidores da infraestrutura do cliente, configura os cenários de detecção para os serviços em produção (SSH, Nginx, API, painel admin), implanta os bouncers de bloqueio (Nginx bouncer, Cloudflare bouncer, iptables bouncer) e configura o dashboard web para visualização de ataques bloqueados em tempo real.",
    differentials: [
      "Inteligência coletiva de +100 mil servidores: IPs maliciosos bloqueados antes do primeiro ataque ao seu servidor",
      "Análise comportamental em camada de aplicação — detecta o que firewalls estáticos não conseguem ver",
      "Bouncers para Nginx, Traefik, Cloudflare e iptables: o bloqueio acontece no ponto certo da pilha",
      "Dashboard web com histórico completo de ataques bloqueados e mapa geográfico de origem",
      "Evolução do Fail2ban: mesma filosofia, com coordenação entre servidores e inteligência global",
    ],
    comingSoon: false,
    icon: ShieldCheck,
    ...SERVICE_TONES.success,
    heroImage: null,
    heroImageAlt: "CrowdSec — proteção colaborativa contra ataques e IPs maliciosos",
    metaTitle: "CrowdSec Self-Hosted — Proteção contra Ataques e IPs Maliciosos — PaperMoon",
    metaDescription:
      "A PaperMoon instala o CrowdSec na sua infraestrutura: detecção de ataques (SSH, web, APIs), bloqueio automático via bouncers e inteligência de ameaças colaborativa com milhões de sensores globais.",
    papermoonDoes: [
      "Instalação do CrowdSec Agent em todos os servidores Linux da sua infraestrutura",
      "Configuração de cenários de detecção: brute-force SSH, ataques web, exploração de CVEs",
      "Configuração de bouncers: Nginx (HTTP 403), iptables (bloqueio de IP), Cloudflare",
      "Integração de logs: SSH, Nginx, Apache, Traefik, aplicações custom",
      "Dashboard local via CrowdSec Console ou integração com Grafana",
      "Configuração de alertas e relatórios de ameaças por e-mail ou Slack",
      "Documentação de operação e treinamento da equipe de TI",
    ],
    clientDoes: [
      "Fornecer acesso SSH aos servidores onde o CrowdSec será instalado",
      "Definir política de bloqueio: duração de ban, whitelist de IPs internos",
      "Aprovar integração com a rede colaborativa CrowdSec para compartilhamento de IPs",
      "Gerenciar whitelists e decisões de bloqueio manual após entrega",
    ],
    steps: [
      {
        num: "01",
        title: "Auditoria da infraestrutura",
        description:
          "Mapeamos todos os servidores, serviços expostos e fontes de log disponíveis. Identificamos os vetores de ataque mais relevantes para definir os cenários de detecção prioritários.",
      },
      {
        num: "02",
        title: "Instalação do agente e cenários",
        description:
          "Instalamos o CrowdSec Agent em cada servidor e configuramos os parsers de log e cenários de detecção: SSH, Nginx/Apache, APIs e CVEs conhecidos. Em horas, os primeiros IPs maliciosos já são detectados.",
      },
      {
        num: "03",
        title: "Configuração dos bouncers",
        description:
          "Instalamos os bouncers que executam o bloqueio: iptables (bloqueio de IP na camada de rede), Nginx/Traefik (retorno 403 na camada HTTP) ou integração com Cloudflare para bloquear na borda.",
      },
      {
        num: "04",
        title: "Dashboard e alertas",
        description:
          "Configuramos dashboard de métricas (CrowdSec Console ou Grafana) e alertas em tempo real para ataques detectados. Entregamos documentação e treinamos a equipe na leitura das decisões.",
      },
    ],
    featureGroups: [
      {
        title: "Detecção de ameaças",
        items: [
          "Brute-force SSH, RDP, FTP e painéis admin web",
          "Scan de portas e fingerprinting de serviços",
          "Exploração de CVEs conhecidos em tempo real",
          "Flood de requisições HTTP (DDoS de camada 7)",
          "Crawlers maliciosos, bots de spam e scrapers agressivos",
        ],
      },
      {
        title: "Bloqueio e resposta",
        items: [
          "Bloqueio automático de IP via iptables ou nftables",
          "Integração com Nginx/Traefik para retorno 403 sem consumo de recursos",
          "Bouncer Cloudflare para bloqueio na borda CDN",
          "Decisões com tempo configurável: 1h, 24h, permanente",
          "Whitelist de IPs internos, escritórios e VPNs",
        ],
      },
      {
        title: "Inteligência colaborativa",
        items: [
          "Acesso à blocklist da rede global CrowdSec (milhões de IPs)",
          "Seu servidor contribui com IPs detectados (opt-in configurável)",
          "Reputação de IP em tempo real antes do primeiro ataque chegar",
          "Listas de terceiros: Tor exit nodes, VPNs conhecidas, hosting abusivo",
          "API REST para consultar reputação de IPs programaticamente",
        ],
      },
    ],
    screenshots: [],
    faqs: [
      {
        q: "Qual a diferença entre CrowdSec e Fail2ban?",
        a: "Fail2ban analisa logs localmente e bloqueia por IP — simples e eficaz, mas sem contexto global. CrowdSec adiciona detecção comportamental mais sofisticada, múltiplos bouncers simultâneos e acesso à inteligência coletiva de milhões de sensores globais — o IP de um atacante identificado em outro país já chega bloqueado na sua rede antes do primeiro ataque.",
      },
      {
        q: "O CrowdSec envia dados da minha rede para fora?",
        a: "Por padrão, o CrowdSec compartilha com a rede colaborativa apenas os IPs atacantes detectados (não dados de conteúdo, usuários ou logs). Esse compartilhamento pode ser desativado — o produto continua funcionando normalmente só com detecção local. A PaperMoon documenta e configura conforme a política de privacidade da empresa.",
      },
      {
        q: "CrowdSec substitui o firewall?",
        a: "Não — é complementar. O firewall (iptables, UFW, security groups) bloqueia portas e protocolos. O CrowdSec analisa o comportamento em nível de aplicação e bloqueia IPs dinamicamente com base em padrões de ataque — algo que firewalls estáticos não fazem. Os dois devem existir juntos.",
      },
      {
        q: "Funciona com Nginx, Traefik e outros proxies reversos?",
        a: "Sim. O CrowdSec tem bouncers para Nginx, Traefik, Caddy, Apache, HAProxy e Cloudflare. O bouncer HTTP retorna 403 ou redirect para captcha antes que a requisição chegue à aplicação — sem consumir recursos do backend.",
      },
      {
        q: "Como funciona a cobrança?",
        a: "A instalação, configuração de cenários e bouncers, dashboard e treinamento são cobrados como projeto único. CrowdSec é open-source e a rede colaborativa tem tier gratuito. O cliente paga apenas os servidores onde o agente roda.",
      },
    ],
    prerequisites: [
      "Servidores Linux com Ubuntu 20.04+ ou Debian 10+ (agente roda em qualquer serviço exposto à internet)",
      "Acesso SSH a todos os servidores onde o CrowdSec será instalado",
      "Lista de serviços expostos: SSH, Nginx, APIs, painéis admin",
      "Definição de política de bloqueio: duração de ban e IPs a colocar em whitelist",
    ],
  },
];

export function getService(slug: string): ServiceContent | undefined {
  return SERVICES.find((s) => s.slug === slug);
}

export const ACTIVE_SERVICES = SERVICES.filter((s) => !s.comingSoon);
export const COMING_SOON_SERVICES = SERVICES.filter((s) => s.comingSoon);
