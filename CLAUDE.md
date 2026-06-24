# CLAUDE.md — PaperMoon Backend

Este arquivo contém as instruções completas para construir o backend da PaperMoon do zero.
Leia tudo antes de criar qualquer arquivo.

---

## Visão Geral do Projeto

Backend SaaS multi-tenant da PaperMoon, construído com Django REST Framework.
Gerencia clientes (tenants), faturamento via Asaas, licenciamento de API Keys,
e integração com Chatwoot para suporte.

**Stack:**
- Python 3.12
- Django 5.x + Django REST Framework
- PostgreSQL 16
- Redis 7
- Celery 5
- Simple JWT (autenticação)
- Docker + Docker Compose

---

## Estrutura de Diretórios a Criar

```
papermoon_backend/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── core/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── celery_app.py
│
├── shared/
│   ├── __init__.py
│   ├── models.py
│   ├── renderers.py
│   ├── exceptions.py
│   └── tasks.py
│
└── apps/
    ├── accounts/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── serializers.py
    │   ├── views.py
    │   └── urls.py
    │
    ├── customers/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── interfaces.py
    │   ├── repositories.py
    │   ├── services.py
    │   ├── serializers.py
    │   ├── views_admin.py
    │   ├── views_client.py
    │   └── urls.py
    │
    ├── billing/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── commands.py
    │   ├── queries.py
    │   ├── tasks.py
    │   ├── views.py
    │   ├── urls.py
    │   └── gateway/
    │       ├── __init__.py
    │       ├── interfaces.py
    │       └── asaas_adapter.py
    │
    ├── licensing/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── commands.py
    │   ├── tasks.py
    │   ├── views.py
    │   └── urls.py
    │
    └── support/
        ├── __init__.py
        ├── client.py
        ├── commands.py
        └── tasks.py
```

---

## Regras de Arquitetura (Seguir Rigorosamente)

### 1. SOLID e Inversão de Dependência
- Views nunca contêm lógica de negócio. Apenas validam entrada e chamam services/commands.
- Services/Commands nunca importam diretamente o ORM. Sempre usam o Repository.
- Repositories implementam a interface definida em `interfaces.py`.

### 2. Padrão de Resposta Unificado
Toda resposta da API deve seguir este contrato, implementado em `shared/renderers.py`:

```json
// Sucesso
{
  "success": true,
  "data": { ... },
  "error": null
}

// Erro
{
  "success": false,
  "data": null,
  "error": {
    "code": "string_snake_case",
    "message": "Mensagem legível para o usuário.",
    "details": ["lista de detalhes opcionais"]
  }
}
```

### 3. Transactional Outbox
- Toda ação que precisa notificar sistemas externos (Chatwoot, n8n) deve gravar
  um `OutboxEvent` na mesma `transaction.atomic()` da operação principal.
- Nunca fazer chamadas HTTP síncronas dentro de services ou commands.
- O Celery processa o Outbox de forma assíncrona e resiliente.

### 4. Multi-Tenant
- Todo modelo de negócio deve ter FK para `Customer`.
- Views de cliente (`views_client.py`) filtram SEMPRE pelo customer do usuário logado.
- Views de admin (`views_admin.py`) requerem `is_staff=True`.

---

## Detalhamento de Cada Arquivo

### `requirements.txt`
```
Django==5.1
djangorestframework==3.15
djangorestframework-simplejwt==5.3
celery==5.4
redis==5.0
psycopg2-binary==2.9
django-environ==0.11
requests==2.32
# dev/test
factory-boy==3.3
pytest-django==4.8
```

### `docker-compose.yml`
Subir 5 serviços:
1. `db` — PostgreSQL 16, porta 5432
2. `redis` — Redis 7 Alpine, porta 6379
3. `web` — Django, porta 8000, depende de db e redis
4. `worker` — Celery worker, mesmo Dockerfile do web, comando `celery -A core.celery_app worker -l info`
5. `beat` — Celery beat, mesmo Dockerfile do web, comando `celery -A core.celery_app beat -l info`

Sem o serviço `beat`, nenhuma task agendada (scan_overdue_invoices, cleanup_old_outbox_events) vai executar.

### `core/settings.py`
- Usar `django-environ` para ler `.env`
- INSTALLED_APPS deve incluir: `rest_framework`, `rest_framework_simplejwt`,
  `rest_framework_simplejwt.token_blacklist`, `corsheaders`,
  `shared`, `apps.accounts`, `apps.customers`, `apps.billing`,
  `apps.licensing`, `apps.support`
- Definir `AUTH_USER_MODEL = 'accounts.CustomUser'` — obrigatório, sem isso o Django ignora o CustomUser
- Configurar DEFAULT_RENDERER_CLASSES para usar `shared.renderers.UnifiedResponseRenderer`
- Configurar `DEFAULT_PAGINATION_CLASS = 'rest_framework.pagination.PageNumberPagination'` e `PAGE_SIZE = 20`
- Configurar SIMPLE_JWT com access token de 1 hora e refresh de 7 dias
- Configurar CELERY_BROKER_URL e CELERY_RESULT_BACKEND apontando para Redis
- Adicionar `corsheaders.middleware.CorsMiddleware` no topo de MIDDLEWARE
- Configurar `CORS_ALLOWED_ORIGINS` via env var
- Configurar `LOGGING` com handler stdout e formatter JSON para produção

### `core/celery_app.py`
- Inicializar Celery com app name `papermoon`
- Autodiscover tasks de todos os apps
- Configurar beat_schedule com as seguintes entradas:
  - `cleanup_old_outbox_events` — `shared.tasks.cleanup_old_outbox_events`, todo dia à meia-noite (`crontab(hour=0, minute=0)`)
  - `scan_overdue_invoices` — `apps.billing.tasks.scan_overdue_invoices`, todo dia à meia-noite
  - `process_outbox_events` — `apps.licensing.tasks.process_outbox_events`, a cada 5 segundos (`timedelta(seconds=5)`)
  - `process_support_outbox_events` — `apps.support.tasks.process_outbox_events`, a cada 5 segundos

### `shared/models.py`
Criar modelo `OutboxEvent` com campos:
- `id`: UUIDField, primary_key, default=uuid4
- `event_type`: CharField(255) — ex: `customer.created`, `payment.failed`
- `payload`: JSONField
- `created_at`: DateTimeField(auto_now_add=True)
- `processed`: BooleanField(default=False)
- `processed_at`: DateTimeField(null=True, blank=True)
- `retry_count`: IntegerField(default=0)
- `last_error`: TextField(null=True, blank=True)
- `failed_at`: DateTimeField(null=True, blank=True)

Meta: `db_table = 'shared_outbox_events'`, `ordering = ['created_at']`

### `shared/renderers.py`
Criar classe `UnifiedResponseRenderer` que herda de `JSONRenderer`.
Override do método `render()` para encapsular qualquer resposta no padrão
`{ success, data, error }`.

### `shared/exceptions.py`
Criar handler customizado `custom_exception_handler` para registrar em
`REST_FRAMEWORK['EXCEPTION_HANDLER']`.
Mapear exceções comuns para códigos de erro amigáveis:
- `AuthenticationFailed` → `authentication_failed`
- `PermissionDenied` → `permission_denied`
- `NotFound` → `not_found`
- `ValidationError` → `validation_error`
- Custom `SubscriptionSuspendedException` → `subscription_suspended`

### `shared/tasks.py`
Task Celery `cleanup_old_outbox_events` que deleta eventos com
`processed=True` e `processed_at` há mais de 30 dias.

### `apps/accounts/models.py`
- `CustomUser` herdando `AbstractUser`
- Campos extras: `phone`, `created_at`, `updated_at`
- `USERNAME_FIELD = 'email'`
- `REQUIRED_FIELDS = ['username']`

### `apps/accounts/views.py`
Endpoints usando Simple JWT:
- `POST /api/v1/auth/login/` — retorna access + refresh tokens
- `POST /api/v1/auth/refresh/` — renova access token
- `POST /api/v1/auth/logout/` — blacklist do refresh token
- `GET  /api/v1/auth/me/` — dados do usuário logado + customer + role
- `POST /api/v1/auth/register/` — auto-cadastro (cria CustomUser + OutboxEvent `user.registered`; `AllowAny`; sem Customer — admin provisiona depois)
- `GET  /api/v1/auth/pending-registrations/` — admin: lista usuários sem CustomerProfile (com company_name do OutboxEvent.payload)
- `POST /api/v1/auth/pending-registrations/<user_id>/provision/` — admin: cria Customer+CustomerProfile para usuário pendente
- `POST /api/v1/auth/password-reset/` — solicitar redefinição de senha
- `POST /api/v1/auth/password-reset/confirm/` — confirmar nova senha
- `POST /api/v1/auth/change-password/` — trocar senha (autenticado)

### `apps/customers/models.py`
Dois modelos:
1. `Customer` — representa a empresa (tenant)
   - `id`: UUID
   - `company_name`: CharField
   - `document`: CharField (CNPJ)
   - `status`: CharField, choices: `active`, `suspended`, `cancelled`
   - `created_at`, `updated_at`

2. `CustomerProfile` — vínculo entre usuário e empresa
   - `user`: FK para CustomUser
   - `customer`: FK para Customer
   - `role`: CharField, choices: `owner`, `admin`, `member`

### `apps/customers/interfaces.py`
Classe abstrata `AbstractCustomerRepository` com métodos:
- `get_by_id(customer_id: UUID) -> Customer`
- `get_all() -> QuerySet`
- `create(data: dict) -> Customer`
- `update(customer_id: UUID, data: dict) -> Customer`
- `suspend(customer_id: UUID) -> Customer`

### `apps/customers/repositories.py`
Classe `DjangoCustomerRepository` implementando `AbstractCustomerRepository`
usando o ORM do Django.

### `apps/customers/services.py`
Classe `CustomerService` recebendo o repository via injeção no `__init__`.
Métodos:
- `create_customer(data)` — cria o Customer e grava `OutboxEvent` com
  `event_type='customer.created'` na mesma transação
- `suspend_customer(customer_id)` — muda status para `suspended` e grava
  `OutboxEvent` com `event_type='customer.suspended'`

### `apps/customers/views_admin.py`
Requer `IsAdminUser`. Endpoints:
- `GET /api/v1/admin/customers/` — lista todos os customers
- `POST /api/v1/admin/customers/` — cria novo customer
- `GET /api/v1/admin/customers/<id>/` — detalhe
- `PATCH /api/v1/admin/customers/<id>/suspend/` — suspende

### `apps/customers/views_client.py`
Requer `IsAuthenticated`. Filtra sempre pelo customer do usuário logado.
Endpoints:
- `GET /api/v1/client/me/` — dados do customer do usuário logado
- `PATCH /api/v1/client/me/` — atualiza dados cadastrais
- `GET /api/v1/client/invoices/` — lista faturas do customer logado (usar `billing/queries.py`)
- `GET /api/v1/client/api-keys/` — lista ApiKeys do customer logado
- `POST /api/v1/client/api-keys/` — gera nova ApiKey
- `DELETE /api/v1/client/api-keys/<id>/` — revoga ApiKey (deve invalidar cache Redis)

### `apps/billing/models.py`
Modelo `Invoice`:
- `id`: UUID
- `customer`: FK para Customer
- `amount`: DecimalField
- `status`: CharField, choices: `pending`, `paid`, `overdue`, `cancelled`
- `due_date`: DateField
- `asaas_id`: CharField (ID externo do Asaas)
- `created_at`, `updated_at`

### `apps/billing/gateway/interfaces.py`
Classe abstrata `AbstractPaymentGateway` com métodos:
- `create_charge(customer, invoice) -> dict`
- `get_charge_status(asaas_id: str) -> str`
- `cancel_charge(asaas_id: str) -> bool`

### `apps/billing/gateway/asaas_adapter.py`
Classe `AsaasGateway` implementando `AbstractPaymentGateway`.
Usar `requests` para chamadas HTTP ao endpoint `https://api.asaas.com/v3`.
Ler `ASAAS_API_KEY` das settings.

### `apps/billing/commands.py`
- `ProcessPaymentCommand(invoice_id)` — processa pagamento via gateway,
  atualiza Invoice e grava OutboxEvent `payment.processed`
- `MarkOverdueCommand(invoice_id)` — marca fatura como `overdue`,
  grava OutboxEvent `payment.failed`

### `apps/billing/queries.py`
Queries diretas sem passar por services/repositories (CQRS para leitura):
- `get_financial_metrics(customer_id)` — retorna total pago, pendente, vencido
- `list_invoices(customer_id, filters)` — lista faturas com paginação

### `apps/billing/tasks.py`
Task Celery `scan_overdue_invoices` — roda diariamente, busca faturas com
`status=pending` e `due_date < hoje`, executa `MarkOverdueCommand` para cada uma.

### `apps/billing/views.py`
- `POST /api/v1/webhooks/asaas/` — endpoint público (sem autenticação JWT),
  mas deve validar o header `asaas-access-token` contra `settings.ASAAS_WEBHOOK_TOKEN`.
  Retornar 403 imediatamente se o token não bater — sem isso qualquer pessoa pode confirmar faturas fictícias.
  Após validação, despacha para o Command correspondente (payment confirmed, payment overdue).

### `apps/licensing/models.py`
Modelo `ApiKey`:
- `id`: UUID
- `customer`: FK para Customer
- `key`: CharField único, gerado automaticamente (usar `secrets.token_urlsafe(32)`)
- `is_active`: BooleanField(default=True)
- `created_at`, `revoked_at`

Modelo `LicenseQuota`:
- `customer`: OneToOneField para Customer
- `max_api_calls`: IntegerField(default=10000)
- `used_api_calls`: IntegerField(default=0)
- `reset_at`: DateTimeField

### `apps/licensing/tasks.py`
Consumidor do Outbox — task `process_outbox_events`:
- Roda a cada 5 segundos
- Busca `OutboxEvent` com `processed=False` usando `select_for_update(skip_locked=True)` dentro de `transaction.atomic()` — evita que múltiplos workers processem o mesmo evento simultaneamente
- Para `event_type='customer.suspended'`: desativa todas as ApiKeys do customer
- Para `event_type='customer.created'`: cria LicenseQuota padrão
- Marca evento como `processed=True` com `processed_at=now()`
- Em caso de erro: incrementa `retry_count`, salva `last_error`, define `failed_at`
- Se `retry_count >= 5`: para de tentar e loga o erro

### `apps/licensing/views.py`
- `GET /api/v1/validate-key/` — endpoint público ultra rápido
  Recebe `?key=xxx` no query param, retorna se a chave é válida e a quota restante.
  Sem autenticação, otimizado para ser chamado pelo n8n.
  **Obrigatório:** cache Redis com TTL de 60 segundos (chave: `apikey:{key_hash}`).
  Invalidar o cache quando a ApiKey for revogada ou a quota resetada.
  Incrementar `used_api_calls` com `F('used_api_calls') + 1` (operação atômica) — nunca ler e somar manualmente.

### `apps/support/client.py`
Classe `ChatwootClient` com métodos HTTP:
- `suspend_agents(customer_id)` — desativa operadores do customer no Chatwoot
- `reactivate_agents(customer_id)` — reativa operadores
Ler `CHATWOOT_API_URL` e `CHATWOOT_API_KEY` das settings.

### `apps/support/commands.py`
- `ProvisionCustomerCommand(customer_id)` — cria workspace no Chatwoot via client
- `SuspendAccessCommand(customer_id)` — suspende acesso via client

### `apps/support/tasks.py`
Consumidor do Outbox para eventos de suporte:
- `event_type='customer.suspended'` → executa `SuspendAccessCommand`
- `event_type='customer.created'` → executa `ProvisionCustomerCommand`
Mesma lógica de retry e `select_for_update(skip_locked=True)` do `licensing/tasks.py`.

**Nota arquitetural:** em versões futuras, considerar consolidar os consumers de `licensing` e `support`
em um único dispatcher em `shared/tasks.py` que roteia por `event_type` para evitar polling duplo do banco.

---

## Apps Adicionados Após a Fundação (Fase 4+)

A fundação original cobre `accounts`, `customers`, `billing`, `licensing` e `support`.
Os apps abaixo foram adicionados no roadmap Fase 4 e estão em `INSTALLED_APPS` e em produção:

- **`apps/products`** — `Product`, `Pricing`, `ServiceComponent`. Catálogo de produtos e planos de
  preço configuráveis, substitui o antigo `apps/plans` (removido — vestigial do modelo pré-pivot).
- **`apps/subscriptions`** — `Subscription`, `License`, `ServiceAccess`. Assinatura de um customer a
  um produto, com renovação (`renewal.py`), proration de troca de plano e provisionamento de acessos
  por serviço. Segue o mesmo padrão repository/commands/queries de `customers`/`billing`.
- **`apps/provisioning`** — adapters por serviço (`chatwoot.py`, `glpi.py`, `zabbix.py`, `n8n.py`,
  `evolution_api.py`, `meta_api.py`, `nextcloud.py`, `proxmox.py`, `aapanel.py`, `truenas.py`,
  `rustdesk.py`) + `registry.py` e `handlers.py` que reagem a eventos do Outbox
  (`subscription.created`, `service_access.provision`, etc.) para criar/revogar acesso ao serviço.
  Todos os provisioners implementam `AbstractProvisioner` e fazem graceful fallback (log-only) quando
  as credenciais não estão configuradas.
- **`apps/notifications`** — `Notification` (in-app) + `handlers.py`/`registry.py`: registry central
  que roteia `event_type` do Outbox para handlers de e-mail e notificação in-app (cobrança vencendo,
  pagamento confirmado, assinatura expirando, etc.). Inclui o handler `user.registered` que notifica
  o admin por e-mail a cada novo auto-cadastro.
- **`apps/audit`** — `AuditLog`. Registra quem fez o quê e quando (admin actions, mudanças de estado),
  exposto em `GET /api/v1/admin/audit-logs/`.
- **`apps/cms`** — `ServicePage` (OneToOneField → `Product`) com modelos aninhados: `ServiceStep`,
  `ServiceFAQ`, `ServiceResponsibility`, `ServiceFeatureGroup`, `ServiceFeatureItem`, `ServiceImage`.
  Imagens convertidas para WebP via Pillow no `pre_save`. Endpoints públicos:
  - `GET /api/v1/cms/services/` — lista de slugs
  - `GET /api/v1/cms/services/<slug>/` — conteúdo completo de uma página de serviço
  - `POST /api/v1/cms/revalidate/` — dispara revalidação ISR do Next.js via Celery (admin only)
  Integra com Next.js ISR: `revalidate: 60` como safety net + on-demand via `revalidatePath()`.

## Auto-cadastro e Fluxo de Provisionamento

O fluxo de entrada de novos clientes sem interação manual da equipe comercial:
1. Usuário acessa `/register` → `POST /api/v1/auth/register/` → cria `CustomUser` + `OutboxEvent(user.registered)`
2. Celery processa `user.registered` → `notify_admin_new_registration` envia e-mail ao admin (`ADMIN_NOTIFICATION_EMAIL`)
3. Admin acessa backoffice `/backoffice/customers` → seção "Cadastros pendentes" mostra usuários sem Customer
4. Admin clica "Provisionar" → modal pré-preenchido com `company_name` do OutboxEvent → `POST /api/v1/auth/pending-registrations/<id>/provision/`
5. Customer + CustomerProfile criados → usuário na tela `/onboarding` é redirecionado automaticamente (polling de `/auth/me` a cada 10s)

---

## Rotas Globais (`core/urls.py`)

Exemplo inicial da fundação (cobre só os 5 apps acima):

```python
urlpatterns = [
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/admin/', include('apps.customers.urls_admin')),
    path('api/v1/client/', include('apps.customers.urls_client')),
    path('api/v1/billing/', include('apps.billing.urls')),
    path('api/v1/licensing/', include('apps.licensing.urls')),
    path('api/v1/webhooks/', include('apps.billing.urls_webhooks')),
]
```

O app `customers` deve ter dois arquivos de rotas separados: `urls_admin.py` (aponta para `views_admin.py`) e `urls_client.py` (aponta para `views_client.py`). O app `billing` deve ter `urls.py` para faturas e `urls_webhooks.py` exclusivo para o endpoint `/webhooks/asaas/`.

> A lista completa e atual de rotas (incluindo `products`, `subscriptions`, `notifications`, `audit`)
> está em `backend/core/urls.py` — não duplicada aqui para evitar desatualização. Referência de API
> com todos os endpoints: `docs/backend/api.md`.

---

## Variáveis de Ambiente (`.env.example`)

```
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgres://papermoon:papermoon@db:5432/papermoon
REDIS_URL=redis://redis:6379/0
ASAAS_API_KEY=your-asaas-api-key
ASAAS_WEBHOOK_TOKEN=your-asaas-webhook-token
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_API_KEY=your-chatwoot-api-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## Ordem de Criação Recomendada

1. `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.env.example`
2. `core/` — settings, urls, celery_app
3. `shared/` — models (OutboxEvent), renderers, exceptions, tasks
4. `apps/accounts/` — CustomUser, JWT views
5. `apps/customers/` — models, interfaces, repositories, services, views
6. `apps/billing/` — models, gateway, commands, queries, tasks, views
7. `apps/licensing/` — models, commands, tasks, views
8. `apps/support/` — client, commands, tasks
9. Migrations: `python manage.py makemigrations && python manage.py migrate`

---

## Observações Finais

- Use type hints em todos os métodos.
- Nunca fazer `import *`.
- Toda FK deve ter `on_delete=models.PROTECT` (exceto onde fizer sentido CASCADE).
- Indexes no banco: `OutboxEvent.processed`, `ApiKey.key`, `Invoice.status + due_date`.
- Comentários apenas quando o **porquê** não é óbvio (restrições ocultas, workarounds). Não descrever o que o código faz.

---

## Roadmap de Desenvolvimento

### Fase 0 — Fundação
> Sistema rodando localmente com todos os módulos

- [x] Infra: `requirements.txt`, `Dockerfile`, `docker-compose.yml` (5 serviços: db, redis, web, worker, beat)
- [x] `core/`: settings, urls, celery_app com beat_schedule completo
- [x] `shared/`: OutboxEvent, renderer, exception handler
- [x] `apps/accounts/`: CustomUser + `AUTH_USER_MODEL`, JWT (login/refresh/logout + blacklist)
- [x] `apps/customers/`: models, interfaces, repository, service, views admin+client
- [x] `apps/billing/`: Invoice, gateway Asaas, commands, queries, views, webhook com verificação de assinatura
- [x] `apps/licensing/`: ApiKey, LicenseQuota, validate-key com cache Redis e F() atômico
- [x] `apps/support/`: ChatwootClient, commands, tasks

### Fase 1 — Correções críticas (antes de qualquer teste externo)
> Nenhum bug de produção óbvio

- [x] `select_for_update(skip_locked=True)` em todos os consumers do Outbox
- [x] Verificação do `asaas-access-token` no webhook
- [x] Cache Redis no `validate-key` com invalidação ao revogar chave
- [x] `F()` expression no incremento de `used_api_calls`
- [x] Paginação global configurada no DRF settings
- [x] Health check: `GET /health/` com status de DB, Redis e Celery

### Fase 2 — Hardening de segurança e observabilidade
> Pronto para receber tráfego real

- [x] Rate limiting nos endpoints de auth (login/refresh)
- [x] Logging estruturado (JSON) para stdout
- [x] Sentry para captura de exceptions em produção
- [x] Máquina de estados do Customer — validar transições no Service
- [x] Split de settings: `base.py`, `local.py`, `production.py`
- [x] Django Admin — registrar Customer, Invoice, ApiKey, OutboxEvent

### Fase 3 — Developer experience e CI
> Time consegue contribuir com confiança

- [x] Documentação OpenAPI com `drf-spectacular` (Swagger UI)
- [x] Testes unitários e de integração completos
- [x] GitHub Actions: lint (ruff), type check (mypy), testes, build Docker
- [x] `Makefile` com `make dev`, `make test`, `make migrate`, `make shell`
- [x] `pre-commit` hooks: ruff + mypy antes de cada commit

### Fase 4 — Features de crescimento
> Produto com mais valor

- [x] Planos de assinatura com limites configuráveis por plano
- [x] Convite de usuários para o tenant (endpoint + e-mail)
- [x] Notificações por e-mail (cobrança vencendo, pagamento confirmado)
- [x] Reativação de customer suspendido
- [x] Audit log — quem fez o quê e quando (crítico para compliance)
- [x] Soft delete em Customer e Invoice (campo `deleted_at`)
- [x] Dashboard de métricas: MRR, churn, uso de API por período
- [x] CMS de páginas de serviço (`apps/cms`) com upload WebP e integração ISR
- [x] Auto-cadastro (`POST /api/v1/auth/register/`) + fluxo de provisionamento backoffice
- [x] Notificação de admin por e-mail a cada novo cadastro (`user.registered`)
- [x] Histórico diário de uso de API (`DailyApiUsage`) + gráfico no dashboard

---

## Estratégia de Testes

- **Unitários** (`tests/unit/`): testar Services e Commands com repositórios mockados (usar `unittest.mock`). Focar em lógica de negócio isolada do ORM.
- **Integração** (`tests/integration/`): testar Views com banco de dados real (usar `TestCase` do Django com SQLite em memória). Cobrir os fluxos principais: criar customer, processar pagamento, validar API Key.
- **Não mockar o banco** nos testes de integração — testar o repositório real para evitar divergência entre mock e produção.
- Usar `factory_boy` para geração de fixtures.
- Rodar com `python manage.py test` ou `pytest` com `pytest-django`. 
