# API Reference — PaperMoon Backend

> Documentação interativa disponível em `http://localhost:8000/api/docs/` (Swagger UI) e `http://localhost:8000/api/redoc/` (ReDoc).

## Base URL

```
http://localhost:8000/api/v1                  # dev — acesso direto ao django-api
https://app.papermoon.com.br/api/proxy/v1         # prod — via BFF do Next.js (injeta o JWT)
https://webhooks.papermoon.com.br/api/v1          # prod — exceção: só /webhooks/asaas/, acesso direto ao django-api
```

## Autenticação

Endpoints protegidos requerem:

```
Authorization: Bearer <access_token>
```

O frontend usa cookies httpOnly via BFF — o header é injetado pelo proxy Next.js.

## Padrão de Resposta

```json
// Sucesso
{ "success": true, "data": { ... }, "error": null }

// Erro
{ "success": false, "data": null, "error": { "code": "snake_case", "message": "...", "details": [] } }
```

**Códigos de erro:**

| Código | HTTP | Situação |
|--------|------|----------|
| `authentication_failed` | 401 | Token inválido ou expirado |
| `permission_denied` | 403 | Sem permissão |
| `not_found` | 404 | Recurso não encontrado |
| `validation_error` | 400 | Dados inválidos |
| `invalid_transition` | 400 | Transição de estado inválida |
| `subscription_suspended` | 403 | Customer suspenso |

---

## Auth

### `POST /auth/login/`
Retorna access + refresh tokens.

**Body:** `{ "email": "...", "password": "..." }`

**Response 200:** `{ "access": "...", "refresh": "..." }`

### `POST /auth/refresh/`
Renova o access token.

**Body:** `{ "refresh": "..." }`

### `POST /auth/logout/`
Blacklista o refresh token.

**Body:** `{ "refresh": "..." }`

### `GET /auth/me/`
Retorna dados do usuário autenticado + customer vinculado + papel.

**Response:**
```json
{
  "user": { "id": "...", "email": "...", "username": "...", "is_staff": false },
  "customer": { "id": "...", "company_name": "...", "status": "active", ... },
  "role": "owner"
}
```

### `POST /auth/password-reset/`
Envia e-mail de redefinição de senha. Sempre retorna 200 (não revela se o e-mail existe).

**Body:** `{ "email": "user@exemplo.com" }`

### `POST /auth/password-reset/confirm/`
Redefine a senha usando o link recebido por e-mail.

**Body:** `{ "uid": "...", "token": "...", "password": "nova_senha" }`

### `POST /auth/change-password/`
Altera a senha do usuário autenticado.

**Body:** `{ "current_password": "...", "new_password": "..." }`

### `POST /auth/register/`
Auto-cadastro público. Cria `CustomUser` e emite `OutboxEvent(user.registered)` que dispara e-mail de notificação ao admin.

**Body:** `{ "email": "...", "username": "...", "password": "...", "company_name": "..." }`

**Auth:** `AllowAny` — sem Customer vinculado até o admin provisionar.

### `GET /auth/pending-registrations/`
Lista usuários sem `CustomerProfile` (cadastros aguardando provisionamento). Inclui `company_name` do payload do OutboxEvent.

**Auth:** `is_staff=True`

### `POST /auth/pending-registrations/<user_id>/provision/`
Cria `Customer` + `CustomerProfile` para o usuário pendente.

**Body:** `{ "company_name": "Empresa Ltda", "document": "12.345.678/0001-90" }`

**Auth:** `is_staff=True`

---

## Convites

### `POST /invitations/accept/`
Endpoint **público**. Aceita um convite e cria a conta do novo usuário.

**Body:** `{ "token": "...", "password": "..." }`

**Response 200:** `{ "message": "...", "customer_id": "...", "role": "member" }`

---

## Admin — Customers

> Requer `is_staff=True`

### `GET /admin/customers/`
Lista todos os customers (paginado). Suporta `?status=active&search=empresa&page=1`.

### `POST /admin/customers/`
Cria novo customer.

**Body:** `{ "company_name": "Empresa Ltda", "document": "12.345.678/0001-90" }`

### `GET /admin/customers/<id>/`
Detalhe de um customer.

### `POST /admin/customers/<id>/suspend/`
Suspende o customer. Dispara `customer.suspended` no Outbox.

### `POST /admin/customers/<id>/reactivate/`
Reativa um customer suspenso. Dispara `customer.reactivated` no Outbox.

### `POST /admin/customers/<id>/cancel/`
Cancela o customer (estado terminal). Dispara `customer.cancelled` no Outbox.

### `DELETE /admin/customers/<id>/delete/`
Soft-delete: marca `deleted_at` sem remover do banco.

### `GET /admin/metrics/`
Retorna métricas de clientes.

---

## Admin — Assinaturas

> Requer `is_staff=True`

### `GET /admin/subscriptions/`
Lista todas as assinaturas. Suporta `?status=active&customer_id=...&page=1&ordering=-created_at`.

### `POST /admin/subscriptions/`
Cria uma assinatura manualmente para um customer.

**Body:** `{ "customer_id": "...", "product_id": "...", "pricing_id": "..." }`

**Response 201:** assinatura criada com status `active`.

### `GET /admin/subscriptions/<id>/`
Detalhe de uma assinatura.

### `POST /admin/subscriptions/<id>/suspend/`
Suspende uma assinatura.

### `POST /admin/subscriptions/<id>/cancel/`
Cancela uma assinatura.

### `POST /admin/subscriptions/<id>/renew/`
Renova uma assinatura expirada.

### `POST /admin/subscriptions/<id>/change-plan/`
Muda o plano de uma assinatura.

**Body:** `{ "pricing_id": "..." }`

### `GET /admin/subscriptions/<id>/services/`
Lista os serviços de uma assinatura.

### `GET /admin/service-accesses/<id>/`
Detalhe de um service access.

### `POST /admin/service-accesses/<id>/reprovision/`
Força o reprovisionamento de um serviço que falhou.

---

## Admin — Produtos

> Requer `is_staff=True`

### `GET /admin/products/`
Lista todos os produtos.

### `POST /admin/products/`
Cria um novo produto.

**Body:** `{ "name": "Starter", "slug": "starter", "description": "...", "is_active": true }`

### `GET /admin/products/<id>/`
Detalhe de um produto.

### `PATCH /admin/products/<id>/`
Atualiza nome, descrição ou status ativo.

### `GET /admin/products/<id>/pricings/`
Lista os planos de preço do produto.

### `POST /admin/products/<id>/pricings/`
Adiciona um plano de preço.

**Body:** `{ "billing_cycle": "monthly", "amount": "299.00", "trial_days": 7, "max_api_calls": 10000, "max_users": 5, "is_active": true }`

### `GET /admin/products/<id>/components/`
Lista os componentes de serviço do produto.

### `POST /admin/products/<id>/components/`
Adiciona um componente de serviço.

**Body:** `{ "service_key": "chatwoot", "config": {} }`

---

## Admin — Faturas

> Requer `is_staff=True`

### `GET /admin/billing/invoices/`
Lista todas as faturas. Suporta `?status=overdue&customer_id=...&page=1`.

### `DELETE /admin/billing/invoices/<id>/`
Soft-delete de uma fatura (oculta da plataforma).

---

## Admin — Métricas de Billing

> Requer `is_staff=True`

### `GET /admin/billing/metrics/mrr/`
Retorna MRR, ARR, churn rate e receita por plano.

**Response:**
```json
{
  "mrr": 14970.00,
  "arr": 179640.00,
  "active_customers": 45,
  "new_customers": 3,
  "churned_customers": 1,
  "churn_rate": 2.2,
  "at_risk_count": 5,
  "revenue_by_plan": [{ "plan": "Starter", "revenue": 8970.0, "customer_count": 30 }],
  "monthly_revenue": [{ "month": "2026-06", "revenue": 14970.0 }]
}
```

### `GET /admin/billing/metrics/api-usage/`
Lista o uso de API calls por customer.

**Response:** `[ { "customer_id": "...", "company_name": "...", "used_api_calls": 4231, "max_api_calls": 10000, "usage_pct": 42.31, "reset_at": "..." } ]`

---

## Admin — Audit Log

> Requer `is_staff=True`

### `GET /admin/audit-logs/`
Lista o audit log. Suporta `?resource_type=customer&action=customer.suspended&page=1`.

**Response (paginado):**
```json
{
  "count": 1240,
  "results": [
    {
      "id": "...",
      "action": "customer.suspended",
      "resource_type": "customer",
      "resource_id": "...",
      "user": "admin@papermoon.com",
      "ip_address": "200.100.x.x",
      "metadata": {},
      "created_at": "2026-06-12T14:00:00Z"
    }
  ]
}
```

---

## Client — Perfil e Empresa

> Requer autenticação. Dados filtrados pelo customer do usuário logado.

### `GET /client/me/`
Dados cadastrais do customer.

### `PATCH /client/me/`
Atualiza `company_name`.

**Body:** `{ "company_name": "Novo Nome" }`

### `GET /client/metrics/`
Métricas financeiras do customer.

**Response:** `{ "total_paid": 897.00, "total_pending": 299.00, "total_overdue": 0.00 }`

### `GET /client/quota/`
Uso de API calls do customer.

**Response:**
```json
{
  "used_api_calls": 4231,
  "max_api_calls": 10000,
  "reset_at": "2026-07-01T00:00:00Z",
  "usage_pct": 42.31,
  "plan_name": "Starter",
  "plan_slug": "starter",
  "billing_cycle": "monthly"
}
```

---

## Client — Assinaturas

### `GET /client/subscriptions/`
Lista as assinaturas do customer.

### `GET /client/subscriptions/<id>/`
Detalhe de uma assinatura.

### `POST /client/subscriptions/`
Ativa um novo produto (cria assinatura).

**Body:** `{ "product_id": "...", "pricing_id": "..." }`

### `POST /client/subscriptions/<id>/reactivate/`
Reativa uma assinatura suspensa.

### `POST /client/subscriptions/<id>/cancel/`
Cancela uma assinatura.

**Body:** `{ "reason": "client_requested" }` (opcional)

### `POST /client/subscriptions/<id>/change-plan/`
Muda o plano.

**Body:** `{ "pricing_id": "..." }`

### `GET /client/subscriptions/<id>/services/`
Lista os service accesses de uma assinatura.

### `GET /client/subscriptions/validate-license/`
Valida uma licença pelo `key`.

**Params:** `?key=...`

---

## Client — Licenças

### `GET /client/licenses/`
Lista as licenças do customer.

### `GET /client/licenses/<id>/`
Detalhe de uma licença com serviços e progresso de validade.

**Response inclui:** `days_remaining`, `services[]`, `valid_from`, `valid_until`.

---

## Client — Faturas

### `GET /client/invoices/`
Lista as faturas do customer. Suporta `?status=pending&ordering=-due_date&page=1`.

### `GET /client/invoices/export/`
Exporta faturas em CSV.

**Params:** `?status=paid`

---

## Client — Equipe

### `GET /client/team/`
Lista os membros da equipe do customer.

**Response:** `[ { "id": "...", "email": "...", "role": "owner", "joined_at": "...", "is_you": true } ]`

### `PATCH /client/team/<profile_id>/`
Altera o papel de um membro. Requer role `owner` ou `admin`.

**Body:** `{ "role": "admin" }` — aceita `"admin"` ou `"member"`.

> Não é possível alterar o papel do `owner` nem o próprio papel.

### `DELETE /client/team/<profile_id>/`
Remove um membro da equipe. Requer role `owner` ou `admin`.

> Não é possível remover o `owner` nem a si mesmo.

---

## Client — Convites

### `GET /client/invitations/`
Lista os convites enviados.

### `POST /client/invitations/`
Envia um convite por e-mail. Requer role `owner` ou `admin`.

**Body:** `{ "email": "novo@empresa.com", "role": "member" }`

### `DELETE /client/invitations/<id>/`
Revoga um convite pendente. Requer role `owner` ou `admin`.

### `POST /client/invitations/<id>/resend/`
Reenvia um convite pendente **ou expirado** com novo token e nova data de expiração (+7 dias). Requer role `owner` ou `admin`.

**Response 200:** convite atualizado com novo `token` e `expires_at`.

> Útil quando o destinatário perdeu o e-mail original ou o link expirou sem que o convite fosse revogado.

---

## Client — API Keys

### `GET /client/api-keys/`
Lista as API Keys do customer.

### `POST /client/api-keys/`
Gera uma nova API Key.

### `DELETE /client/api-keys/<id>/`
Revoga uma API Key. Invalida o cache Redis da chave.

---

## Client — Notificações

### `GET /client/notifications/`
Lista as notificações. Suporta `?page=1`.

**Response:**
```json
{
  "count": 12,
  "unread_count": 3,
  "num_pages": 1,
  "results": [ { "id": "...", "event_type": "payment.processed", "subject": "Pagamento confirmado", "body": "...", "is_read": false, "created_at": "..." } ]
}
```

### `POST /client/notifications/<id>/read/`
Marca uma notificação como lida.

### `POST /client/notifications/read-all/`
Marca todas as notificações como lidas.

---

## Produtos (Público)

### `GET /products/catalog/`
Lista os produtos ativos com pricings. Não requer autenticação.

---

## Licensing (Público)

### `GET /licensing/validate-key/`
Valida uma API Key e retorna a quota restante. Endpoint ultra-rápido para uso pelo n8n.

**Params:** `?key=<api_key>`

**Response:**
```json
{ "valid": true, "quota_remaining": 9769 }
```

> Cache Redis de 60 segundos por chave. Incremento atômico com `F()`.

---

## Webhooks

### `POST /webhooks/asaas/`
Endpoint **público**. Recebe eventos de pagamento do Asaas.

> **Segurança:** Valida o header `asaas-access-token` contra `ASAAS_WEBHOOK_TOKEN`. Retorna 403 imediatamente se inválido.

**Header obrigatório:** `asaas-access-token: <ASAAS_WEBHOOK_TOKEN>`

**Eventos tratados:**
| Evento Asaas | Ação |
|---|---|
| `PAYMENT_CONFIRMED` / `PAYMENT_RECEIVED` | `ConfirmPaymentCommand` → fatura `paid` + `payment.processed` no Outbox |
| `PAYMENT_OVERDUE` | `MarkOverdueCommand` → fatura `overdue` + `payment.failed` no Outbox |
| `PAYMENT_DELETED` / `PAYMENT_REFUNDED` | `MarkOverdueCommand` |

---

## CMS (Público)

### `GET /cms/services/`
Lista os slugs de todas as páginas de serviço publicadas no CMS.

**Response:** `["chatwoot", "n8n", "glpi", ...]`

### `GET /cms/services/<slug>/`
Retorna o conteúdo completo de uma página de serviço (texto rico, passos, FAQs, galeria de imagens).

**Response:** Objeto `ServicePage` com campos:

```json
{
  "slug": "zabbix",
  "hero_image_url": "https://app.papermoon.com.br/media/...",
  "hero_image_alt": "Painel de monitoramento",
  "tagline": "Visibilidade total da sua infra",
  "description": "Monitore servidores, redes e VMs.",
  "meta_title": "Zabbix — PaperMoon",
  "meta_description": "Monitoramento com Zabbix gerenciado.",
  "papermoon_does": ["Instalacao", "Configuracao", "Observabilidade"],
  "client_does": ["Fornecer acessos", "Validar escopo"],
  "steps": [{ "number": "01", "title": "Levantamento", "description": "Mapeamos.", "order": 1 }],
  "feature_groups": [{ "title": "Monitoramento", "items": [{ "text": "Dashboards", "order": 1 }], "order": 1 }],
  "faqs": [{ "question": "Quanto custa?", "answer": "Consulte.", "order": 1 }],
  "images": [{ "url": "https://app.papermoon.com.br/media/...", "alt": "", "caption": "", "order": 1 }],
  "updated_at": "2026-06-21T12:00:00Z"
}
```

`papermoon_does` e o unico campo suportado para a coluna de responsabilidades da plataforma.

> O frontend faz merge deste conteúdo com o conteúdo estático de `services-content.ts` — o CMS tem prioridade sobre os campos que estão preenchidos.

## CMS (Admin)

> Requer `is_staff=True`

### `GET /admin/cms/pages/`
Lista todos os produtos ativos com status de página CMS.

### `GET /admin/cms/pages/<slug>/`
Retorna os dados completos da página CMS para edição.

### `PATCH /admin/cms/pages/<slug>/`
Atualiza a página CMS e substitui integralmente as coleções aninhadas enviadas.

**Body:** objeto `ServicePageAdmin`, incluindo `responsibilities`, `steps`, `feature_groups` e `faqs`.

### `POST /admin/cms/revalidate/<slug>/`
Dispara revalidação ISR do Next.js via Celery para um serviço específico.

---

## Health Check

### `GET /health/`
Verifica status de DB, Redis e Celery.

**Response:**
```json
{ "success": true, "data": { "status": "ok", "db": "ok", "redis": "ok" }, "error": null }
```
