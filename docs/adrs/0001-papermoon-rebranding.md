# ADR 0001: Rebranding Oficial para PaperMoon

## Status

Accepted

## Contexto

O repositorio ja foi renomeado para `papermoon`, mas o ecossistema ainda possui referencias legadas a `Riise`, `Riisen`, `Riise Core`, `Riise Platform` e variacoes em documentacao, metadados, seeds, defaults de infraestrutura e componentes de UI.

Essa divergencia cria risco de:

- inconsistencias de marca entre frontend, backend e operacao;
- acoplamento indevido entre branding e implementacao tecnica;
- defaults inseguros ou confusos em ambientes novos;
- dificuldade de manutencao, auditoria e onboarding.

## Decisao

PaperMoon passa a ser a unica identidade oficial do produto em toda nova decisao tecnica, arquitetural, visual e documental.

O rebranding sera feito de forma gradual, com compatibilidade temporaria apenas onde houver risco operacional ou dependencia externa.

## Diretrizes

1. Todo novo artefato deve usar `PaperMoon` como identidade publica.
2. Novos recursos de infraestrutura devem seguir convencoes `papermoon-*`, `papermoon.*` e `PAPERMOON_*`.
3. Regras de negocio, modelos de dominio e contratos de API nao devem depender de nomes de marca.
4. Design system deve usar design tokens e variaveis CSS, sem cores hard-coded em componentes.
5. O backend permanece como fonte unica de verdade para regras, validacoes criticas e contratos versionados.
6. Toda funcionalidade deve assumir contexto multi-tenant.

## Estrategia de Migracao

### Fase 1: Fonte oficial

- Atualizar README, metadata, ADRs e documentacao principal para PaperMoon.
- Registrar backlog de migracao de nomes legados.
- Introduzir tokens PaperMoon com compatibilidade para tokens existentes.

### Fase 2: Superficie publica

- Trocar branding em paginas publicas, e-mails, sitemap, SEO e OpenAPI.
- Atualizar defaults publicos de dominio e remetente para placeholders neutros ou PaperMoon.
- Renomear componentes visuais claramente legados.

### Fase 3: Infraestrutura e configuracao

- Migrar nomes de redes, volumes, containers e exemplos operacionais para o padrao PaperMoon.
- Introduzir prefixos `PAPERMOON_*` para novas variaveis de ambiente.
- Manter fallback temporario para nomes legados quando houver necessidade de compatibilidade.

### Fase 4: Limpeza final

- Remover aliases, defaults e identificadores legados apos janela de transicao.
- Atualizar testes, seeds e scripts residuais.

## Consequencias

### Positivas

- Coerencia entre produto, operacao e documentacao.
- Menor acoplamento entre marca e implementacao.
- Melhor governanca arquitetural para um SaaS multi-tenant.
- Base mais preparada para crescimento enterprise e multiplos ambientes.

### Custos

- Necessidade de migracao gradual em deploys existentes.
- Convivencia temporaria com nomes legados em seeds, testes e alguns componentes.
- Esforco adicional de documentacao e validacao operacional.

## Fora de Escopo Imediato

- Renomeacao completa de toda seed data historica.
- Troca simultanea de todos os service names do Docker Compose.
- Substituicao imediata de todos os domínios legados em ambientes ja provisionados.

## Referencias

- `README.md`
- `docs/deployment.md`
- `docs/frontend/architecture.md`
- `docs/checklists/papermoon-rebranding-checklist.md`
