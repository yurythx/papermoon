# PaperMoon Platform

PaperMoon e um ecossistema SaaS multi-tenant para gerenciamento de clientes, faturamento, licenciamento, CMS e integracoes operacionais.

> `PaperMoon` e a unica identidade valida do produto. Documentacao, metadados e interfaces devem refletir apenas essa identidade.

**Stack:** Python 3.12 · Django 5 · DRF · PostgreSQL 16 · Redis 7 · Celery 5 · Next.js 14 · TypeScript · Tailwind CSS

---

## Quickstart — Desenvolvimento

```bash
cp backend/.env.example backend/.env
make dev        # sobe todos os servicos (Django, Next.js, Postgres, Redis, Celery)
make migrate    # aplica as migrations
make seed       # popula dados de demonstracao
```

Acesse:

| Servico | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API Django | http://localhost:8000 |
| Swagger UI | http://localhost:8000/api/v1/docs/ |
| MailHog | http://localhost:8025 |

Credenciais seed:

| Conta | Senha | Papel |
|---|---|---|
| admin@papermoon.com | admin123 | superadmin |
| owner@acme.com | demo123 | owner |
| owner@techcorp.com | demo123 | owner |

---

## Quickstart — Stack de Produção Local

Para testar o stack de produção (Gunicorn, Redis com senha, Celery workers, Next.js standalone) na máquina de desenvolvimento:

```bash
make local-prod-setup   # gera .env.production, cria rede Docker, builda e sobe tudo
make prod-superuser     # cria superusuário admin
make local-prod-logs    # acompanhar logs
make local-prod-down    # parar
```

Acesse em http://localhost:3000 (frontend) e http://localhost:8000/admin/ (Django admin).

---

## Deploy em Produção

```bash
# Na VPS (primeiro deploy):
git clone https://github.com/yurythx/papermoon.git /opt/papermoon
cd /opt/papermoon
sudo bash setup.sh      # instala Docker, gera segredos, pergunta domínio/e-mail/Asaas, faz deploy
```

Deployos subsequentes são automáticos via GitHub Actions (push para `main` → CI → CD).
Guia completo: `docs/deployment.md`.

---

## Principios

- Backend como `single source of truth` para regras de negocio.
- Arquitetura orientada a dominio, desacoplada de branding.
- Multi-tenancy obrigatorio em qualquer nova funcionalidade.
- Observabilidade, seguranca e operacao em producao tratadas como requisitos de arquitetura.
- Design system baseado em tokens, sem uso de cores hard-coded em componentes.

---

## Estrutura

```text
backend/
├── core/            # settings, urls, celery
├── shared/          # renderer, exceptions, permissions, logging, health
└── apps/
    ├── accounts/
    ├── customers/
    ├── billing/
    ├── licensing/
    ├── subscriptions/
    ├── products/
    ├── provisioning/
    ├── notifications/
    ├── cms/
    ├── support/
    └── audit/

frontend/
├── src/app/         # Next.js App Router
│   ├── api/         # BFF route handlers (proxy + cookie auth)
│   ├── dashboard/   # area do cliente
│   └── backoffice/  # area administrativa
└── e2e/             # testes Playwright

docs/
├── backend/
├── frontend/
├── adrs/
└── checklists/
```

Regras de arquitetura:

- **Views** validam entrada e delegam para commands, services ou use cases.
- **Commands/Services** nao devem acoplar regras de negocio ao transporte HTTP.
- **CQRS** separa leituras (`queries.py`) de escritas (commands + repositories).
- **Transactional Outbox** desacopla integracoes externas do fluxo transacional primario.
- **BFF** centraliza autenticacao, proxy e politicas de acesso no Next.js.
- **Branding** deve permanecer desacoplado de namespaces, domínios tecnicos e regras de negocio.

---

## Documentacao

- Arquitetura backend: `docs/backend/architecture.md`
- Arquitetura frontend: `docs/frontend/architecture.md`
- Deploy: `docs/deployment.md`
- ADR de rebranding: `docs/adrs/0001-papermoon-rebranding.md`
- Checklist de migracao: `docs/checklists/papermoon-rebranding-checklist.md`
