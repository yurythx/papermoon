# ADR 0003: Expansão de stack para observabilidade, IaC, feature flags e serviço poliglota

## Status

Proposed

## Contexto

A PaperMoon já demonstra padrões de engenharia de nível sênior (CQRS, Outbox transacional,
BFF, multi-tenancy, CI/CD com rollback). O objetivo agora é duplo: (1) fechar lacunas reais
de operação que a arquitetura atual expõe, e (2) adicionar tecnologias ao portfólio —
mas apenas onde resolvem um problema que o sistema já tem, não por currículo.

Quatro iniciativas foram escolhidas. Cada uma é avaliada aqui pelo problema real que resolve,
não só pelo valor de portfólio — isso é dito explicitamente porque uma delas (gRPC) é a mais
discutível sob o critério de necessidade pura.

## Decisão

Todas as quatro entram no roadmap (Fase 5 do `CLAUDE.md`), na ordem de prioridade abaixo.
Ordem reflete relação esforço/risco vs. valor — não é obrigatório seguir em sequência, mas
cada uma depois da primeira assume que a anterior está em produção.

### 5.1 OpenTelemetry + tracing distribuído (prioridade mais alta) — Implementado

> Backend implementado (Django, Celery, Postgres, Redis, requests + linking do
> OutboxEvent). Detalhes completos, como rodar localmente e status de produção:
> `docs/backend/observability.md`. Frontend (Next.js/`@vercel/otel`) ainda não
> feito — próximo incremento desta seção, não bloqueia o resto.

**Problema real que resolve:** a cadeia `View → OutboxEvent → Celery task → Provisioner →
API externa` é hoje impossível de rastrear ponta a ponta. Quando um `customer.created`
falha silenciosamente em algum provisioner, a única pista é `OutboxEvent.last_error` — sem
contexto de quanto tempo levou, quais outros eventos do mesmo request foram afetados, ou
correlação com o request HTTP que originou tudo.

**Desenho:**
- `opentelemetry-instrumentation-django`, `-celery`, `-psycopg2`, `-redis`,
  `-requests` no backend. A instrumentação de `-requests` é a que mais importa na
  prática: todos os 19 `apps/provisioning/*` chamam APIs externas (Chatwoot, GLPI,
  Zabbix, Keycloak...) via `requests` — hoje uma chamada lenta ou instável em qualquer
  um deles é invisível até virar `OutboxEvent.last_error`.
- Exportação OTLP para um collector (Grafana Tempo ou equivalente self-hosted — não SaaS,
  para não introduzir custo recorrente).
- Trace ID propagado para linkar o request original à task assíncrona que o processa.
  Implementado como colunas dedicadas `trace_id`/`span_id` no `OutboxEvent` (não
  dentro de `payload`, que é dado de negócio dos handlers) — capturadas automaticamente
  em `save()`, sem tocar nenhum dos 30+ call sites que criam `OutboxEvent` pelo código.
- Next.js: `@vercel/otel` ou instrumentação manual nas rotas BFF, propagando `traceparent`
  para o Django via header.

**Por que é a prioridade 1:** menor risco (é só instrumentação, não muda contrato de nada),
maior valor operacional imediato, e é a skill mais procurada no mercado hoje das quatro.

### 5.2 Feature flags self-hosted (Unleash)

**Problema real que resolve:** `apps/products` e `apps/subscriptions` já modelam planos e
limites por customer, mas todo rollout de feature nova é tudo-ou-nada via deploy. Não há
como liberar uma feature para um subconjunto de tenants (beta, plano específico) sem
condicional hardcoded.

**Desenho:**
- Unleash self-hosted (imagem oficial, mais um serviço no `docker-compose.prod.yml`),
  não SaaS — consistente com o resto da infra (tudo self-hosted na VPS).
  Alternativa mais simples: uma tabela `FeatureFlag` própria em `shared/` (customer_id +
  flag_key + enabled) se Unleash for overkill para o volume de flags real. Decidir no
  momento da implementação, com base em quantas flags distintas o produto realmente precisa.
- Avaliação de flag acontece no backend (single source of truth, mesmo princípio já
  documentado no README), nunca no frontend.

### 5.3 Terraform para provisionamento de infra

**Problema real que resolve:** `setup.sh` (17KB de bash) provisiona VPS, gera segredos,
configura DNS/domínio manualmente. Funciona, mas não é idempotente nem auditável — rodar
duas vezes ou revisar "o que mudou" na infra não tem o mesmo rigor que existe no código da
aplicação (que tem CI, lint, review).

**Desenho:**
- Terraform não substitui `deploy.sh` (esse continua cuidando de build/migrate/rollback da
  aplicação — é uma responsabilidade diferente). Terraform assume a camada abaixo:
  criação da VPS/DNS (se o provedor tiver API — ex. Hetzner, DigitalOcean) e, potencialmente,
  registro do client OIDC no Keycloak (Terraform tem provider para Keycloak — fecha o ciclo
  com a ADR 0002).
- Escopo inicial pequeno e deliberado: só o que hoje é feito manualmente ou por bash frágil.
  Não migrar Docker Compose para Terraform — não é o problema que o Terraform resolve bem aqui.
- **State remoto desde o primeiro commit**: backend remoto com locking (ex. S3 compatível
  self-hosted + DynamoDB-like lock, ou Terraform Cloud free tier) e `*.tfstate` no
  `.gitignore` desde o início — o state guarda segredos em texto plano (ex. `client_secret`
  do client OIDC criado via provider Keycloak), então nunca pode ir para o Git, no mesmo
  espírito de por que `.env` já é ignorado neste repo.

### 5.4 Serviço Go + gRPC para `/validate-key` (menor prioridade, avaliar antes de comprometer)

**Problema que alega resolver:** `GET /api/v1/validate-key/` já é descrito no `CLAUDE.md`
como "endpoint público ultra rápido... otimizado para n8n", com cache Redis e `F()` atômico.
É o único endpoint do sistema com requisito de latência explícito, o que o torna o único
candidato honesto para extração — os outros 100+ endpoints não têm essa pressão.

**Avaliação honesta:** no volume atual de tráfego, Django + cache Redis provavelmente já
atende a latência necessária. Reescrever em Go só se justifica se (a) o objetivo é
demonstrar competência poliglota no portfólio — o que é uma motivação válida, mas deve ser
nomeada como tal — ou (b) medição real (via 5.1, OTel) mostrar que o endpoint está mesmo
no limite. **Decisão: implementar depois de instrumentar 5.1 e observar o p99 real do
endpoint em produção.** Se o p99 já for saudável, este item vira "portfolio-only" e deve
ser tratado como um exercício isolado, não como refactor do caminho crítico.

**Desenho (se seguir adiante):**
- Serviço Go novo, `services/validate-key/`, expõe gRPC internamente (chamado por um
  handler fino no Django/nginx, ou diretamente pelo n8n se ele suportar gRPC — caso
  contrário, mantém um pequeno HTTP wrapper).
- Lê o mesmo Redis (`apikey:{key_hash}`) que o Django já popula — **não duplica a fonte de
  verdade**, o Go service é read-through cache, não dono do dado.
  `ApiKey`/`LicenseQuota` continuam sendo tabelas Postgres geridas exclusivamente pelo Django.
- Incremento de `used_api_calls` continua passando pelo Django (via fila ou chamada
  interna) para não criar duas implementações da regra atômica `F()`.

## Consequências

### Positivas

- Cada iniciativa amarrada a uma dor concreta e nomeada — fácil de explicar em entrevista
  sem soar como "adicionei X porque estava na moda".
- Ordem de prioridade evita comprometer com a peça mais arriscada (Go/gRPC) antes de ter
  dados (OTel) que validem se ela é necessária.

### Negativas / trade-offs

- Unleash e o coletor OTel são novos serviços para operar (mais um item no `docker-compose.prod.yml`,
  mais um ponto de monitoramento).
- Serviço Go, se implementado, é a primeira peça não-Python do runtime — aumenta a superfície
  de conhecimento necessária pra qualquer pessoa dar manutenção no sistema.
