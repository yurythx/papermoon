# Arquitetura do Backend — PaperMoon

## Visão Geral

Backend SaaS multi-tenant construído com Django REST Framework. Gerencia clientes (tenants), faturamento via Asaas, licenciamento de API Keys, notificações por e-mail, convites de equipe e integração com Chatwoot.

## Stack

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| Framework | Django 5.1 + Django REST Framework 3.15 |
| Banco | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Tasks assíncronas | Celery 5 + Celery Beat |
| Autenticação | Simple JWT (RS256, access 1h, refresh 7d + blacklist) |
| Docs OpenAPI | drf-spectacular (Swagger UI + ReDoc) |
| Monitoramento | Sentry (só em production) |
| Testes | pytest-django + factory-boy |

## Estrutura de Pastas

```
backend/
├── core/
│   ├── settings/
│   │   ├── base.py          # Configurações comuns (DRF, JWT, Celery, email)
│   │   ├── local.py         # Dev: DEBUG=True, throttle relaxado, MailHog
│   │   └── production.py    # Prod: Gunicorn, HTTPS, HSTS, Sentry
│   ├── urls.py              # Roteamento global
│   ├── celery_app.py        # Celery app + beat_schedule
│   └── wsgi.py
│
├── shared/
│   ├── models.py            # OutboxEvent
│   ├── renderers.py         # UnifiedResponseRenderer
│   ├── exceptions.py        # custom_exception_handler
│   ├── views.py             # HealthCheckView
│   └── urls.py              # GET /health/
│
└── apps/
    ├── accounts/            # Autenticação — CustomUser + JWT
    ├── audit/               # Audit log de todas as ações
    ├── billing/             # Faturas + gateway Asaas + métricas MRR
    ├── customers/           # Tenants — Customer, CustomerProfile, Invitations
    ├── licensing/           # API Keys + LicenseQuota + validate-key
    ├── notifications/       # E-mails transacionais + in-app notifications
    │   ├── registry.py      # Dispatcher de handlers por event_type
    │   └── handlers.py      # Handlers: email_payment_confirmed, etc.
    ├── cms/                 # Páginas de serviço editáveis no backoffice; merge com conteúdo estático no Next.js
    ├── products/            # Catálogo de produtos + ServiceComponents + Pricings
    ├── provisioning/        # Adapters por serviço (chatwoot, n8n, glpi, zabbix, proxmox…) + registry + handlers
    ├── subscriptions/       # Assinaturas + Licenças + ServiceAccesses + renovação + proration
    └── support/             # Integração Chatwoot (legado — novos provisionamentos usam apps/provisioning)
```

## Padrões Aplicados

### Repository Pattern
```
View → Service/Command → Repository (interface) → Django ORM
```
Views não tocam o ORM. Toda persistência passa por um Repository que implementa uma interface abstrata.

### Transactional Outbox
Toda integração externa usa o padrão Outbox:
1. Operação principal + `OutboxEvent` gravados na mesma `transaction.atomic()`
2. Celery processa o Outbox a cada 5s com `select_for_update(skip_locked=True)`
3. Retry automático até 5 tentativas

### CQRS (parcial)
- **Commands** (`commands.py`): escrita + evento, sempre em `@transaction.atomic`
- **Queries** (`queries.py`): leituras puras sem efeitos colaterais

### Event-Driven
O registry em `apps/notifications/registry.py` roteia eventos para handlers. `NotificationsConfig.ready()`
importa `apps/licensing/handlers.py`, `apps/notifications/handlers.py` e `apps/support/handlers.py`;
`apps/notifications/handlers.py` por sua vez importa `apps/provisioning/handlers.py` — então um único
import chain registra os 4 módulos de handlers no startup.

| event_type | Handlers ativos | Módulo |
|---|---|---|
| `customer.created` | `provision_asaas_customer`, `email_customer_created` | notifications |
| `customer.created` | `create_license_quota` | licensing |
| `customer.created` | `provision_chatwoot` | support |
| `customer.suspended` | `email_customer_suspended`, `in_app_customer_suspended` | notifications |
| `customer.suspended` | `deactivate_api_keys` | licensing |
| `customer.suspended` | `suspend_chatwoot` | support |
| `customer.suspended` | `cascade_suspend_subscriptions` | provisioning |
| `customer.reactivated` | `email_customer_reactivated`, `in_app_customer_reactivated` | notifications |
| `customer.reactivated` | `reactivate_api_keys` | licensing |
| `customer.reactivated` | `reactivate_chatwoot` | support |
| `customer.reactivated` | `cascade_reactivate_subscriptions` | provisioning |
| `customer.cancelled` | `email_customer_cancelled` | notifications |
| `payment.processed` | `email_payment_confirmed`, `renew_subscription_on_payment`, `in_app_payment_confirmed` | notifications |
| `payment.due_soon` | `email_payment_due_soon`, `in_app_payment_due_soon` | notifications |
| `payment.dunning_d3` | `email_dunning_d3`, `in_app_dunning_d3` | notifications |
| `payment.failed` | `email_payment_overdue`, `in_app_payment_overdue` | notifications |
| `charge.registered` | `log_charge_registered` | notifications |
| `renewal_invoice.created` | `register_renewal_charge` | notifications |
| `invitation.created` | `email_invitation` | notifications |
| `invitation.accepted` | `log_invitation_accepted`, `email_invitation_accepted` | notifications |
| `subscription.created` | `email_subscription_created` | notifications |
| `subscription.created` | `sync_quota_from_subscription` | licensing |
| `subscription.created` | `provision_services`, `sync_quota_on_create` | provisioning |
| `subscription.suspended` | `email_subscription_suspended`, `in_app_subscription_suspended` | notifications |
| `subscription.suspended` | `suspend_services` | provisioning |
| `subscription.expired` | `email_subscription_expired`, `in_app_subscription_expired` | notifications |
| `subscription.expired` | `deprovision_services` | provisioning |
| `subscription.cancelled` | `email_subscription_cancelled` | notifications |
| `subscription.cancelled` | `deprovision_services_on_cancel` | provisioning |
| `subscription.renewed` | `email_subscription_renewed`, `in_app_subscription_renewed` | notifications |
| `subscription.renewed` | `reactivate_services`, `sync_quota_on_renewal` | provisioning |
| `subscription.grace_period` | `email_grace_period`, `in_app_grace_period` | notifications |
| `subscription.grace_period` | `notify_grace_period` | provisioning |
| `subscription.expiring_soon` | `email_expiring_soon`, `in_app_expiring_soon` | notifications |
| `subscription.expiring_soon` | `notify_expiring_soon` | provisioning |
| `subscription.plan_changed` | `email_plan_changed`, `in_app_plan_changed` | notifications |
| `quota.warning` | `email_quota_warning` | notifications |
| `service_access.provision` | `provision_single_service` | provisioning |
| `service_access.deprovision` | `deprovision_single_service` | provisioning |

### Multi-Tenant
- Todo modelo de negócio tem FK para `Customer`
- Views client filtram sempre pelo customer do usuário logado (`_resolve_customer()`)
- Views admin requerem `IsAdminUser`

## Fluxo de Estado do Customer

```
ACTIVE ──► SUSPENDED ──► ACTIVE
  │              │
  └──────────────┴──► CANCELLED (terminal)
```

Transições inválidas lançam `ValueError` com `code: "invalid_transition"`.

## Segurança

| Camada | Mecanismo |
|---|---|
| Autenticação | JWT RS256 (access 1h, refresh 7d com blacklist) |
| Webhook Asaas | Header `asaas-access-token` validado contra `ASAAS_WEBHOOK_TOKEN` |
| Rate limiting | DRF throttle: 10/min login, 100/day endpoints anônimos |
| Produção | HTTPS obrigatório, HSTS 1 ano, X-Frame-Options DENY, CSRF SameSite |
| Cookies | `SECURE_COOKIES=false` em dev; `True` automático em prod via Gunicorn |
| Erros | Sentry com traces (só em `production.py`) |

## Celery Beat Schedule

Todas as crontabs usam `timezone = "America/Sao_Paulo"` (UTC-3 em horário padrão).

| Task | Frequência | Descrição |
|---|---|---|
| `process_outbox_events` | a cada 5s | Processa OutboxEvents pendentes com `select_for_update(skip_locked=True)` |
| `scan_overdue_invoices` | diário 00:00 | Marca faturas `pending` vencidas como `overdue` |
| `cleanup_old_outbox_events` | diário 00:00 | Remove OutboxEvents processados há > 30 dias |
| `reset_quota_monthly` | diário 01:00 | Reseta `used_api_calls` de todas as LicenseQuotas |
| `scan_expiring_subscriptions` | diário 00:30 | Move assinaturas `active → grace_period` e `grace_period → expired` |
| `scan_expiring_soon` | diário 08:00 | Emite `subscription.expiring_soon` em D-7, D-3, D-1 |
| `generate_renewal_invoices` | diário 09:00 | Cria faturas de renovação 3 dias antes do vencimento |
| `scan_quota_warnings` | diário 10:00 | Emite `quota.warning` ao atingir 80% e 90% de uso |

## Variáveis de Ambiente

### Backend (`backend/.env`)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SECRET_KEY` | Sim | Chave secreta do Django |
| `DATABASE_URL` | Sim | URL do PostgreSQL |
| `REDIS_URL` | Sim | URL do Redis |
| `DJANGO_SETTINGS_MODULE` | Sim | `core.settings.local` ou `core.settings.production` |
| `FRONTEND_URL` | Sim | Base URL do frontend (usado em links de e-mail) |
| `ASAAS_API_KEY` | Prod | Chave da API Asaas |
| `ASAAS_WEBHOOK_TOKEN` | Prod | Token de validação do webhook Asaas |
| `CHATWOOT_API_URL` | Prod | URL base da instância Chatwoot |
| `CHATWOOT_API_KEY` | Prod | Access token do usuário Chatwoot |
| `JWT_PRIVATE_KEY` | Prod | Chave RSA privada para assinar JWTs |
| `JWT_PUBLIC_KEY` | Prod | Chave RSA pública para verificar JWTs |
| `SENTRY_DSN` | Não | DSN do Sentry (só ativa em `production.py`) |
| `EMAIL_BACKEND` | Não | Backend de e-mail (SMTP em prod, console em dev) |
| `EMAIL_HOST` | Não | Host SMTP (`mailhog` em dev, SES/SendGrid em prod) |
| `EMAIL_PORT` | Não | Porta SMTP (1025 para MailHog, 587/465 para prod) |
| `EMAIL_HOST_USER` | Não | Usuário SMTP |
| `EMAIL_HOST_PASSWORD` | Não | Senha SMTP |
| `EMAIL_USE_TLS` | Não | `True` para prod, `False` para MailHog |
| `DEFAULT_FROM_EMAIL` | Não | Remetente padrão (`noreply@papermoon.com`) |
| `REDIS_PASSWORD` | Prod | Senha do Redis em produção |
| `POSTGRES_PASSWORD` | Prod | Senha do PostgreSQL em produção |
| `FLOWER_USER` | Não | Usuário do Flower (default: `admin`) |
| `FLOWER_PASSWORD` | Não | Senha do Flower (default: `papermoon2024`) |

### Frontend (`frontend/.env.local` ou variáveis do container)

| Variável | Descrição |
|---|---|
| `DJANGO_INTERNAL_URL` | URL interna do Django (ex: `http://django-api:8000/api/v1`) |
| `NEXT_PUBLIC_SENTRY_DSN` | DSN do Sentry para o frontend |
| `NEXT_PUBLIC_SITE_URL` | URL pública do frontend (ex: `https://app.papermoon.com.br`) |
| `SECURE_COOKIES` | `false` em dev (sem HTTPS), omitir em prod |
