# Guia de Desenvolvimento — PaperMoon

Setup local completo do zero para um novo desenvolvedor.

---

## Pré-requisitos

- Docker Engine 24+ e Docker Compose v2
- Git
- `make` (GNU Make)
- Node.js 20+ (opcional — só para rodar frontend fora do Docker)

---

## 1. Clonar o repositório

```bash
git clone https://github.com/your-org/papermoon.git
cd papermoon
```

---

## 2. Subir o ambiente de desenvolvimento

```bash
# Sobe todos os containers (postgres, redis, django-api, celery-worker, celery-beat, mailhog, nextjs)
make up

# Verificar status
make ps
```

O comando `make up` equivale a `docker compose up -d`.

---

## 2.1 Para que serve cada container

Nem sempre voce precisa de todos os containers ao mesmo tempo. A stack foi separada entre servicos obrigatorios para a aplicacao funcionar, servicos necessarios para processamento assíncrono e servicos auxiliares de desenvolvimento.

| Servico | Container | Obrigatorio | Funcao |
|---|---|---|---|
| PostgreSQL | `papermoon-postgres-dev` | Sim | Banco principal da aplicacao. Guarda tenants, usuarios, clientes, faturamento, CMS, auditoria e configuracoes. |
| Redis | `papermoon-redis-dev` | Sim | Broker e cache. Sustenta Celery, filas, invalidacoes e partes da operacao assíncrona. |
| Django API | `papermoon-api-dev` | Sim | Backend principal em Django/DRF. Expoe a API, admin, docs e regras de negocio. |
| Next.js | `papermoon-web-dev` | Sim | Frontend principal da plataforma. Serve a interface publica, dashboard e backoffice. |
| Celery Worker | `papermoon-worker-dev` | Depende do fluxo | Executa tarefas em background: e-mails, notificacoes, integracoes, reprocessamentos e jobs assíncronos. |
| Celery Beat | `papermoon-worker-beat-dev` | Depende do fluxo | Dispara tarefas agendadas. Necessario para rotinas periodicas como jobs programados, reconciliacoes e manutencao automatica. |
| Flower | `papermoon-monitoring-dev` | Nao | Painel de monitoramento do Celery. Util para inspecionar filas, workers, retries e tasks travadas. |
| MailHog | `papermoon-mailhog-dev` | Nao | SMTP falso para desenvolvimento. Captura e-mails enviados pela aplicacao sem usar provedor real. |

### Leitura pratica

- **Minimo para abrir a aplicacao no navegador:** `postgres`, `redis`, `django-api`, `nextjs`
- **Minimo para validar fluxos com tarefas em background:** adicionar `celery-worker`
- **Minimo para validar rotinas agendadas:** adicionar `celery-beat`
- **Observabilidade de filas em dev:** adicionar `flower`
- **Testar e-mails localmente:** adicionar `mailhog`

### Quando voce pode desligar

- Pode desligar `flower` quase sempre se nao estiver depurando filas.
- Pode desligar `mailhog` se nao estiver testando envio de e-mails.
- Pode desligar `celery-beat` se nao estiver validando agendamentos.
- Pode desligar `celery-worker` apenas se o fluxo que voce esta testando nao depender de tarefas assíncronas.

### Subidas parciais uteis

```bash
# App web sem filas nem email
docker compose up -d postgres redis django-api nextjs

# App web com tarefas em background
docker compose up -d postgres redis django-api celery-worker nextjs

# Stack completa de desenvolvimento
docker compose up -d postgres redis django-api celery-worker celery-beat flower mailhog nextjs
```

### Recomendacao do projeto

- Para desenvolvimento diario de backend/frontend: `postgres`, `redis`, `django-api`, `nextjs`, `celery-worker`
- Para revisar jobs periodicos: adicionar `celery-beat`
- Para investigar filas ou falhas de task: adicionar `flower`
- Para validar e-mails transacionais: adicionar `mailhog`

---

## 3. Aplicar migrations e criar dados de demo

```bash
# Migrations
make migrate

# Seed com dados de demonstração (idempotente — seguro de rodar múltiplas vezes)
make seed
```

O seed cria:
- Superusuário admin: `admin@papermoon.com` / `admin123`
- 5 empresas demo com usuários, assinaturas, faturas, licenças, notificações e audit logs
- Usuários de demo: `owner@acme.com`, `owner@globo.com`, `owner@mega.com` / `demo123`

---

## 4. Verificar os serviços

| Serviço | URL | Descrição |
|---|---|---|
| Frontend (Next.js) | http://localhost:3000 | App principal |
| Django API | http://localhost:8000/api/v1 | REST API |
| Swagger UI | http://localhost:8000/api/docs/ | Documentação interativa |
| ReDoc | http://localhost:8000/api/redoc/ | Docs alternativas |
| Django Admin | http://localhost:8000/admin/ | Admin nativo (login: `admin@papermoon.com`) |
| MailHog | http://localhost:8025 | Caixa de e-mails de dev |
| Flower | http://localhost:5555 | Monitoramento do Celery (admin/papermoon2024) |
| Health Check | http://localhost:8000/health/ | Status DB + Redis |

---

## 5. Desenvolvimento diário

### Backend (Django)

O container `django-api` usa `runserver` com hot-reload e `docker compose watch` para sincronização de arquivos.

```bash
# Ver logs do backend
make logs

# Abrir Django shell
make shell

# Criar nova migration
make migrations

# Rodar testes backend (722 testes)
make test

# Verbose
make test-v

# Com cobertura
make test-cov

# Lint (ruff)
make lint

# Formatar (ruff format)
make fmt

# Type check (mypy)
make typecheck
```

### Frontend (Next.js)

O container `nextjs` roda em modo produção. Para dev com hot-reload, rode fora do Docker:

```bash
# Instalar dependências (apenas na primeira vez)
make frontend

# Hot-reload em http://localhost:3000
make frontend-dev

# Build de produção (inclui type check)
make frontend-build

# Testes unitários/integração (151 testes)
make frontend-test

# Testes E2E com Playwright (requer containers rodando + seed)
make frontend-e2e
```

### Hot-reload completo (backend + workers)

```bash
# Sincroniza arquivos e reinicia Celery automaticamente ao salvar
make watch
```

---

## 6. Variáveis de ambiente

### Backend: `backend/.env`

Gerado automaticamente com o repositório. Valores de dev pré-configurados:

```
DATABASE_URL=postgres://papermoon:papermoon@postgres:5432/papermoon
REDIS_URL=redis://redis:6379/0
FRONTEND_URL=http://localhost:3000
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailhog
EMAIL_PORT=1025
...
```

> Para testar integrações reais (Asaas, Chatwoot), edite `ASAAS_API_KEY` e `CHATWOOT_API_KEY` no `.env`.

### Frontend

O container nextjs lê variáveis do `docker-compose.yml` (seção `environment`). Para rodar localmente fora do Docker, crie `frontend/.env.local`:

```bash
DJANGO_INTERNAL_URL=http://localhost:8000/api/v1
SECURE_COOKIES=false
```

---

## 7. Emails em desenvolvimento

Todos os e-mails transacionais (convites, reset de senha, confirmação de pagamento) são capturados pelo **MailHog** em http://localhost:8025.

Não é necessário configurar nenhum SMTP real em desenvolvimento.

---

## 8. Criar superusuário manualmente

```bash
make superuser
```

---

## 9. Gerar chaves JWT RS256

Necessário apenas se você resetar o banco ou rodar pela primeira vez em produção:

```bash
make generate-jwt-keys
# Copia os valores JWT_PRIVATE_KEY e JWT_PUBLIC_KEY para .env (dev) ou .env.production (prod)
```

Em desenvolvimento o Django usa HS256 como fallback se as chaves RS256 não estiverem configuradas.

---

## 10. Pre-commit hooks

```bash
# Instalar ruff + mypy como hooks de pré-commit
make hooks
```

Após instalação, `git commit` executa lint e type check automaticamente.

---

## 11. Limpeza

```bash
# Parar e remover containers
make down

# Remover .pyc, __pycache__, .coverage
make clean

# Rebuild completo sem cache (útil após mudanças em requirements.txt)
make build
```

---

## 12. Estrutura de testes

### Backend

```bash
backend/tests/
├── unit/           # Services e Commands com repositórios mockados
└── integration/    # Views com banco real (pytest-django, sem SQLite — usa PostgreSQL do Docker)
```

Rodados com `pytest` dentro do container `django-api`. O banco de testes é criado/destruído automaticamente.

### Frontend

```bash
frontend/src/__tests__/
├── unit/           # Funções puras (services.ts, utils.ts)
└── integration/    # Componentes (Vitest + Testing Library + MSW)

frontend/e2e/       # Playwright E2E
```

---

## 13. Flower (Celery monitoring)

```bash
make flower
# Acesse http://localhost:5555 (admin/papermoon2024)
```

---

## Troubleshooting

| Sintoma | Solução |
|---|---|
| `django-api` não sobe | `docker compose logs django-api` — verificar `.env` |
| `make migrate` falha | `make up` primeiro para garantir que postgres está healthy |
| E-mails não chegam no MailHog | Verificar `EMAIL_HOST=mailhog` no `.env`; confirmar container MailHog rodando |
| Erro "stream did not contain valid UTF-8" no build frontend | Arquivo fonte foi corrompido por PowerShell `Set-Content` (encoding ANSI). Usar `Write` do Claude ou editar diretamente |
| Worker Celery não processa tasks | `make logs` para ver `celery-worker`; verificar `REDIS_URL` |
| Port 5433/8000/3000 em uso | Alterar portas em `docker-compose.yml` ou parar o processo conflitante |
