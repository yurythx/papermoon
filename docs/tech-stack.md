# Stack técnica e capacidades

Referência do que está implementado e rodando neste repositório versus tecnologias
que fazem parte do domínio de conhecimento por trás dele e se encaixariam
naturalmente em fases futuras. Escrito pra ser honesto sobre a diferença entre os
dois — nada aqui finge que existe código que não existe.

---

## Em produção neste repositório

### Python / Django

Linguagem e framework do backend inteiro. DRF (Django REST Framework) + Simple JWT
(RS256) pra API e autenticação, Celery + Celery Beat pra processamento assíncrono
(Transactional Outbox), drf-spectacular pra OpenAPI/Swagger, django-filter,
django-environ, Pillow (processamento de imagem no CMS), Sentry SDK. Padrões
aplicados: CQRS, Repository, Service layer, Outbox transacional — ver
`docs/backend/architecture.md`.

### Docker & Docker Compose

Todo o ambiente — dev e produção — roda containerizado. `docker-compose.yml` (dev)
sobe 9 serviços (Postgres, Redis, Jaeger, Django, Celery worker, Celery beat,
Flower, MailHog, Next.js) com healthchecks e hot-reload via `docker compose watch`
no backend. `docker-compose.prod.yml` replica a topologia com Gunicorn, Whitenoise e
segredos via `.env.production`. Build multi-stage no frontend (`deps` → `builder` →
`runner`, imagem final standalone do Next.js). Deploy automatizado via
`deploy.sh` + GitHub Actions (CI → CD com rollback automático em caso de falha de
health check) — ver `docs/deployment.md`.

### TypeScript / Next.js

Frontend inteiro: App Router, padrão BFF (rotas `app/api/*` centralizam auth e
proxy pro Django, tokens nunca tocam o browser), TanStack Query, Zustand,
Tailwind, Playwright (e2e) e Vitest (unit/integration).

---

## Capacidades — conhecimento aplicável, ainda não implementado neste repo

As tecnologias abaixo fazem parte do domínio de infraestrutura/DevOps que este
projeto pratica (ver os 19 `apps/provisioning/*` do backend, que já integram com
GLPI, Zabbix, Proxmox, TrueNAS, Keycloak e outros serviços self-hosted). Ainda não
há um módulo Terraform, playbook Ansible ou serviço Go rodando *dentro* deste
repositório — quando adicionados de verdade, isso será registrado aqui com um
link pro código, não só citado.

### Terraform (Infraestrutura como Código)

Onde se encaixaria: registrar o client OIDC do Keycloak usado pelo SSO de staff
(hoje um passo manual — ver `docs/backend/sso-keycloak-integration.md`, seção
5.1) via o provider `keycloak/keycloak`; e, num escopo maior, provisionamento
declarativo de VPS/DNS em vez do `setup.sh` atual (bash imperativo). Ver
`docs/adrs/0003-portfolio-tech-expansion.md`, seção 5.3, para a análise completa
de escopo e por que o state precisa de backend remoto antes de qualquer uso real.

### Ansible (gerência de configuração)

Onde se encaixaria: complementar o Terraform acima — depois de a infraestrutura
existir, o Ansible cuidaria da configuração do host (instalar Docker Engine,
firewall, deploy da stack) de forma idempotente, como alternativa declarativa ao
`setup.sh`/`deploy.sh` atuais.

### Go

Onde se encaixaria: um serviço satélite para o endpoint `/validate-key`
(licensing), que já é descrito como "ultra rápido, cache Redis, chamado pelo n8n
a cada requisição" — o único endpoint do sistema com pressão de latência real.
Leria a mesma chave que o Django já popula no Redis, sem duplicar a lógica de
quota/licença. Ver `docs/adrs/0003-portfolio-tech-expansion.md`, seção 5.4 — a
própria ADR condiciona essa peça a medir o p99 real primeiro (via OpenTelemetry),
pra não reescrever em Go algo que o cache já resolve.

---

## Referências

- Arquitetura backend: `docs/backend/architecture.md`
- Arquitetura frontend: `docs/frontend/architecture.md`
- Roadmap de expansão (OTel, feature flags, Terraform, Go): `docs/adrs/0003-portfolio-tech-expansion.md`
- Integração SSO (Keycloak): `docs/backend/sso-keycloak-integration.md`
