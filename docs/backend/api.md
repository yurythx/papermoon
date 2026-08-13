# API Reference — PaperMoon Backend

> Documentação interativa disponível em `http://localhost:8000/api/docs/` (Swagger UI) e `http://localhost:8000/api/redoc/` (ReDoc).

## Base URL

```
http://localhost:8000/api/v1                  # dev — acesso direto ao django-api
https://papermoon.cloud/api/proxy/v1          # prod — via BFF do Next.js (injeta o JWT)
https://papermoon.cloud/api/v1/webhooks/asaas/ # prod — exceção: sem JWT, valida o header asaas-access-token
                                                # (domínio único — ver aviso no topo de docs/deployment.md)
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
  "user": { "id": "...", "email": "...", "username": "...", "first_name": "...", "last_name": "...", "is_staff": false },
  "customer": { "id": "...", "company_name": "...", "status": "active", ... },
  "role": "owner",
  "feature_flags": ["beta_widget", "site_wide"]
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

### `GET /auth/sso/login/`
Inicia o fluxo OIDC de SSO (staff only, via Keycloak). Gera `state`/PKCE/`nonce` e
retorna `200 { "authorize_url": "..." }`. **Chamado apenas server-to-server pelo BFF**
(`app/api/auth/sso/route.ts`, que faz o redirect de verdade para o browser) — nunca
diretamente pelo browser. Ver `docs/backend/sso-keycloak-integration.md`.

**Auth:** `AllowAny`. Retorna `503 sso_not_configured` se o SSO estiver desativado ou
incompleto em `SSOConfiguration` (editável em Backoffice → Configurações).

### `POST /auth/sso/callback/`
Troca o `code` recebido do Keycloak pelo `id_token`, valida claims (`iss`, `aud`,
`exp`, `nonce`, assinatura via JWKS) e emite o par JWT de sempre — **só para contas
com `is_staff=True`** (sem JIT provisioning). Chamado pelo BFF
(`app/api/auth/sso/callback/route.ts`), não pelo Keycloak diretamente.

**Body:** `{ "code": "...", "state": "..." }`

**Response 200:** `{ "access": "...", "refresh": "..." }`

**Erros:** `400 invalid_state` (state expirado/reutilizado) · `400 sso_exchange_failed`
(id_token inválido) · `403 sso_account_not_staff` (e-mail não é staff) ·
`503 sso_not_configured`

### `GET /auth/sso/status/`
Endpoint público — só expõe `{ "enabled": true|false }`, nunca issuer/client_id/secret.
Consultado pela tela `/login` (via `GET /api/auth/sso/status` no BFF) pra decidir se
mostra o botão "Entrar com Keycloak". Reflete o toggle do backoffice em até 30s (TTL do
cache — ver `apps/accounts/sso_config.py`).

**Auth:** `AllowAny`

---

## Admin — SSO

> Requer `is_staff=True`. Ver `docs/backend/sso-keycloak-integration.md` para o guia
> completo de configuração (criar client no Keycloak, preencher aqui, testar).

### `GET /admin/sso-config/`
Estado atual da configuração de SSO. `client_secret` nunca é retornado — só
`client_secret_set: bool`.

**Response:** `{ "enabled": bool, "issuer": str, "client_id": str, "client_secret_set": bool, "redirect_uri": str, "updated_at": str|null, "updated_by_email": str|null }`

### `PATCH /admin/sso-config/`
Atualiza a configuração. **PATCH parcial de verdade**: `issuer`/`client_id`/
`client_secret` ausentes do body mantêm o valor já salvo (ex: `{"enabled": false}`
sozinho só desliga o toggle, não apaga o resto). Ativar (`enabled: true`) exige
`issuer` + `client_id` + um `client_secret` (novo ou já salvo) — senão
`400 validation_error`. Grava `AuditLog(sso_config.updated)` sem o valor do segredo.

**Body:** `{ "enabled": bool, "issuer"?: str, "client_id"?: str, "client_secret"?: str }`

### `POST /admin/sso-config/test/`
Testa conectividade com o Keycloak: busca `{issuer}/.well-known/openid-configuration` e
confirma que os endpoints OIDC existem e o `issuer` bate. **Não valida
client_id/client_secret nem faz um login completo** — para isso, use o botão "Entrar
com Keycloak" em `/login` de verdade.

**Body:** `{ "issuer"?: str }` — se omitido, testa o issuer já salvo.

**Response:** `{ "reachable": bool, "message": str }`

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

## Admin — Feature Flags

> Requer `is_staff=True`

### `GET /admin/feature-flags/`
Lista todas as feature flags.

### `POST /admin/feature-flags/`
Cria uma flag.

**Body:**
```json
{
  "key": "beta-widget",
  "name": "Beta widget",
  "description": "Widget experimental do dashboard.",
  "enabled_globally": false,
  "enabled_customer_ids": ["uuid-customer-1", "uuid-customer-2"]
}
```

### `GET /admin/feature-flags/<id>/`
Detalhe de uma flag, incluindo `enabled_customers` (lista `{id, company_name}`).

### `PATCH /admin/feature-flags/<id>/`
Atualização parcial — mesmos campos do POST.

### `DELETE /admin/feature-flags/<id>/`
Remove a flag.

> Resolução: `GET /auth/me/` devolve `feature_flags: string[]` com as keys habilitadas
> pro usuário logado (globais + específicas do customer). Sem rollout por porcentagem —
> ver `apps/flags/services.py`.

---

## Contato (Público)

### `POST /contact/`
Formulário de contato do site público — envia e-mail interno pra
`DEFAULT_FROM_EMAIL`, não persiste nada no banco.

**Body:**
```json
{
  "name": "Fulano de Tal",
  "email": "fulano@empresa.com",
  "phone": "(66) 99999-0000",
  "service": "Chatwoot",
  "message": "Gostaria de um orçamento."
}
```
`phone` e `service` são opcionais.

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
  "hero_image_url": "https://papermoon.cloud/media/...",
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
  "images": [{ "url": "https://papermoon.cloud/media/...", "alt": "", "caption": "", "order": 1 }],
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

## Blog (Público)

### `GET /blog/`
Lista posts com `status=published`, paginado (`PageNumberPagination`, `PAGE_SIZE=20`), ordenado por `-published_at`. Filtro opcional `?tag=<slug>`.

**Response:**
```json
{
  "count": 12,
  "next": "http://.../api/v1/blog/?page=2",
  "previous": null,
  "results": [
    {
      "slug": "como-configurar-sso-com-keycloak",
      "title": "Como configurar SSO com Keycloak",
      "excerpt": "Passo a passo pra integrar...",
      "cover_image_url": "https://papermoon.cloud/media/blog/covers/....webp",
      "cover_image_alt": "Tela de configuração do Keycloak",
      "author_name": "Ana Silva",
      "published_at": "2026-06-21T12:00:00Z",
      "reading_time": 4,
      "tags": [{ "name": "Keycloak", "slug": "keycloak" }, { "name": "SSO", "slug": "sso" }]
    }
  ]
}
```

`reading_time` é estimado no backend por contagem de palavras do `body` (200 palavras/min) — presente em `/blog/` e `/blog/<slug>/` mesmo sem expor o `body` na listagem.

### `GET /blog/<slug>/`
Retorna o post completo (corpo em Markdown + SEO). Um `slug` de rascunho (`status=draft`) responde `404` — nunca vaza conteúdo não publicado, mesmo pra quem tem a URL exata.

**Response:** objeto acima + `body` (Markdown), `meta_title`, `meta_description`.

> **Nota de cache (frontend):** `fetchBlogPost` (`frontend/src/lib/blog.ts`) usa `cache: "no-store"`, sem ISR — o Next.js App Router não invalida de forma confiável o Full Route Cache quando essa rota passa de um render bem-sucedido pra `notFound()` (post despublicado/excluído), nem via `revalidateTag`/`revalidatePath` explícitos nem pela janela passiva de `revalidate`. Confirmado ao vivo contra o build standalone real. `fetchBlogPosts` (listagem) não tem esse problema e mantém `revalidate: 60` + tag `blog-posts`.

## Blog (Admin)

> Requer `is_staff=True`

### `GET /admin/blog/`
Lista todos os posts (rascunho e publicado), paginado. Filtro opcional `?status=draft|published`.

**Response:** lista leve — `id`, `title`, `slug`, `status`, `author_name`, `published_at`, `updated_at`, `tags`.

### `POST /admin/blog/`
Cria um post como `draft`. `author` é sempre o usuário autenticado — não é um campo aceito no body.

**Body:** `title`, `slug`, `excerpt`, `body` (opcional na criação — editado depois).

### `GET /admin/blog/<id>/`
Retorna o post completo pra edição.

### `PATCH /admin/blog/<id>/`
Atualiza qualquer subconjunto de campos, incluindo `status`. Ao transicionar `draft` → `published` pela primeira vez, `published_at` é preenchido automaticamente e nunca mais sobrescrito por publicações subsequentes (republicar não reseta a data original).

**Body opcional:** `tag_names: string[]` — lista de nomes de tags; get-or-create por slug (`django.utils.text.slugify`), então `"Backup"` e `"backup"` resolvem pra mesma tag. Enviar `[]` remove todas as tags do post. Omitir o campo não mexe nas tags atuais.

### `DELETE /admin/blog/<id>/`
Remove o post permanentemente (capa incluída). Dispara a mesma revalidação ISR do save (`apps/blog/signals.py`, `post_delete`) — sem isso, excluir um post publicado não avisava o Next pra purgar `/blog/<slug>`.

### `POST /admin/blog/<id>/cover/`
Upload da imagem de capa (`multipart/form-data`, campo `cover_image`). Convertida para WebP automaticamente (mesmo pipeline do CMS — `apps.cms.services.ImageProcessor`).

### `DELETE /admin/blog/<id>/cover/`
Remove a imagem de capa do post.

### `POST /admin/blog/<id>/body-image/`
Upload de uma imagem pra inserir no corpo em Markdown (`multipart/form-data`, campo `image`; botão de imagem da toolbar do editor). Convertida para WebP, sem model próprio — o Markdown do post já é a fonte de verdade de onde cada imagem é usada. Resposta: `{ "image_url": "https://..." }`.

---

## Health Check

### `GET /health/`
Verifica status de DB, Redis e Celery.

**Response:**
```json
{ "success": true, "data": { "status": "ok", "db": "ok", "redis": "ok" }, "error": null }
```
