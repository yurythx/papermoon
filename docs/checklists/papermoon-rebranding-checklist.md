# Checklist Tecnico de Migracao para PaperMoon

## 1. Branding e conteudo publico

- [x] Atualizar README principal para PaperMoon.
- [x] Atualizar metadata raiz do frontend para PaperMoon.
- [x] Atualizar documentacao-base de arquitetura e deploy.
- [x] Revisar landing page, paginas institucionais, SEO e Open Graph.
- [x] Revisar textos de e-mail e templates HTML.
- [x] Remover referencias publicas a nomenclaturas legadas.

## 2. Design system e UX

- [x] Introduzir tokens oficiais `--papermoon-*` em `globals.css`.
- [x] Remover cores hard-coded de foco e selecao da camada global.
- [ ] Mapear todos os componentes para consumir apenas tokens semanticos.
- [ ] Auditar contraste, focus states e compatibilidade WCAG.
- [ ] Considerar `prefers-color-scheme` como modo padrao quando o risco de regressao for aceitavel.

## 3. Backend e contratos

- [x] Atualizar titulo e descricao do OpenAPI para PaperMoon.
- [x] Atualizar defaults neutros de `FRONTEND_URL` e `DEFAULT_FROM_EMAIL`.
- [x] Revisar seeds, fixtures e factories com identificadores legados.
- [ ] Auditar serializers, handlers e notificacoes que constroem URLs publicas.
- [ ] Formalizar versionamento e naming de APIs sob a governanca PaperMoon.

## 4. Infraestrutura e operacao

- [x] Migrar rede externa legada para `papermoon-network` com plano de compatibilidade.
- [x] Padronizar nomes de containers para `papermoon-api`, `papermoon-web`, `papermoon-worker`, `papermoon-monitoring`.
- [x] Padronizar volumes para `papermoon-data`, `papermoon-media` e `papermoon-backups`.
- [x] Revisar scripts de deploy, compose e CI/CD para remover defaults legados.
- [x] Atualizar dominios de exemplo para placeholders PaperMoon ou valores parametrizados.
- [ ] Executar runbook de migracao de identificadores de banco legados para `papermoon` em producao.

## 5. Variaveis de ambiente

- [ ] Definir politica de migracao de `RIISE_*` e nomes genericos para `PAPERMOON_*`.
- [ ] Introduzir camada de compatibilidade temporaria no backend para leitura dual onde fizer sentido.
- [ ] Atualizar `.env.example` e `.env.production.example` para refletir a estrategia aprovada.
- [ ] Documentar janela de deprecacao e criterios de remocao dos aliases.

## 6. Qualidade e governanca

- [x] Registrar ADR oficial de rebranding.
- [ ] Atualizar diagramas arquiteturais com identidade PaperMoon.
- [x] Revisar testes E2E e integracoes com dados de marca legada.
- [ ] Adicionar checklist de validacao de release para migracoes de branding.
- [ ] Confirmar observabilidade minima para deploys: logs estruturados, health checks, metricas e alertas.
