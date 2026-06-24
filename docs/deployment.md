# Deployment Guide — PaperMoon

Step-by-step checklist for deploying PaperMoon to production.

> Antes de executar o corte, percorra tambem a checklist operacional em
> [production-deploy-checklist.md](file:///c:/Users/yuri.menezes/Desktop/Projetos/papermoon/docs/checklists/production-deploy-checklist.md).

> **Arquitetura de rede:** Este guia usa **Cloudflare Tunnel** como único ponto de entrada.
> Não há Nginx, Caddy ou Let's Encrypt — o TLS é terminado na borda da Cloudflare.
> O cloudflared já está rodando como container no servidor.

---

## Visão Geral da Arquitetura

```
Usuário ──HTTPS──► Cloudflare Edge ──Tunnel──► cloudflared (container)
                                                    │
                                      rede Docker: papermoon-network
                                                    │
                                        ┌───────────┴───────────┐
                                   nextjs:3000          django-api:8000
                                        │                       │
                                   rede Docker: default (interno)
                                        │                       │
                                   celery-worker          postgres/redis
```

- **Dominio publico**: use um hostname PaperMoon, como `app.papermoon.example.com`, como host principal para usuarios/browser. O Next.js
  atua como BFF — todas as chamadas de API do frontend passam por `/api/proxy/*`, que injeta o
  JWT e encaminha internamente para `django-api` pela rede Docker. O backend nunca é exposto
  diretamente para esse tráfego.
- **Exceção: webhook do Asaas.** O proxy BFF exige um JWT de usuário autenticado — o Asaas nunca
  teria esse token. Por isso só o endpoint `/api/v1/webhooks/asaas/` é exposto direto ao
  `django-api` num hostname dedicado, como `webhooks.papermoon.example.com`, protegido pela validacao do
  header `asaas-access-token` (ver `cloudflared/config.yml.example`).
- **Cloudflare** termina TLS, aplica "Always Use HTTPS", gerencia certificados automaticamente.
- **Django** recebe HTTP puro vindo do tunnel. O header `X-Forwarded-Proto: https` (injetado pelo cloudflared) instrui Django a emitir cookies `Secure` corretamente.
- **Nenhuma porta** de `django-api` ou `nextjs` e exposta no host — acesso so pela rede compartilhada do tunnel.

> O Compose usa `papermoon-network` como rede externa compartilhada com o cloudflared. Esse e o unico caminho suportado para o tunnel em producao.

---

## Prerequisites

- Docker Engine 24+ e Docker Compose v2 no servidor
- Cloudflared já rodando como container (instalado previamente)
- Dominios configurados no Cloudflare (`app.papermoon.example.com` para o app, `webhooks.papermoon.example.com`
  só para o webhook do Asaas)
- Conta Asaas com API key de produção
- Instância Chatwoot

---

## 1. Configurar a Rede Docker do Tunnel

Este passo conecta os containers da aplicação à mesma rede Docker do cloudflared.

```bash
# 1. Criar a rede externa preferencial (uma única vez por servidor)
docker network create papermoon-network
# ou: make tunnel-network

# 2. Descobrir o nome do container do cloudflared
docker ps --filter "ancestor=cloudflare/cloudflared" --format "{{.Names}}"
# Exemplo de saída: cloudflared

# 3. Conectar o cloudflared à rede preferencial
docker network connect papermoon-network cloudflared
# ou: make tunnel-connect  (interativo — pede o nome do container)

# Verificar
docker network inspect papermoon-network --format '{{range .Containers}}{{.Name}} {{end}}'
# Deve mostrar: cloudflared
```

---

## 2. Configurar o Tunnel no Cloudflare Dashboard

No painel da Cloudflare → **Zero Trust → Networks → Tunnels → seu tunnel → Configure**:

Adicione as rotas de entrada (ingress rules):

| Hostname | Serviço | Uso |
|---|---|---|
| `app.papermoon.example.com` | `http://nextjs:3000` | App principal — todo o trafego de usuario/browser |
| `webhooks.papermoon.example.com` | `http://django-api:8000` | So o webhook do Asaas (`/api/v1/webhooks/asaas/`) — o BFF exige JWT, entao o Asaas nao pode chamar via `app.papermoon.example.com` |

> Os nomes `django-api` e `nextjs` são service names do Docker Compose. O cloudflared os resolve porque está na mesma rede `papermoon-network`.

---

## 3. Clonar e Configurar

```bash
git clone https://github.com/your-org/papermoon.git /opt/papermoon
cd /opt/papermoon
```

### `.env.production` (na raiz do projeto)

```bash
cp .env.production.example .env.production
# Editar com os valores reais
```

| Variável | Valor de produção |
|---|---|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `False` |
| `DATABASE_URL` | `postgres://<usuario>:<senha>@postgres:5432/<database>` |
| `ALLOWED_HOSTS` | `app.papermoon.example.com,webhooks.papermoon.example.com,django-api` |
| `REDIS_URL` | `redis://:${REDIS_PASSWORD}@redis:6379/0` |
| `REDIS_PASSWORD` | Senha forte gerada aleatoriamente |
| `POSTGRES_PASSWORD` | Senha forte gerada aleatoriamente |
| `CORS_ALLOWED_ORIGINS` | `https://app.papermoon.example.com` |
| `FRONTEND_URL` | `https://app.papermoon.example.com` |
| `ASAAS_API_KEY` | Chave de produção do Asaas |
| `ASAAS_WEBHOOK_TOKEN` | Token secreto para validar webhooks |
| `CHATWOOT_API_URL` | URL da instância Chatwoot |
| `CHATWOOT_API_KEY` | Access token do usuário Chatwoot |
| `JWT_PRIVATE_KEY` | Deixe vazio — gerada automaticamente (ver seção abaixo) |
| `JWT_PUBLIC_KEY` | Deixe vazio — gerada automaticamente |
| `SENTRY_DSN` | DSN do projeto no Sentry (opcional) |

> Se o ambiente ainda estiver com identificadores legados de banco e usuario, mantenha os valores
> atuais ate executar o runbook [db-identifier-migration.md](file:///c:/Users/yuri.menezes/Desktop/Projetos/papermoon/docs/db-identifier-migration.md).

#### Prioridade real das variaveis

Use esta classificacao para decidir o que precisa estar pronto no dia do corte:

- **Obrigatorias para subir a aplicacao**: `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL`, `REDIS_PASSWORD`, `REDIS_URL`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`, `REVALIDATE_SECRET`, `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`.
- **Obrigatorias para operacao comercial**: `ASAAS_API_KEY`, `ASAAS_WEBHOOK_TOKEN`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
- **Opcionais com degradacao controlada**: `CHATWOOT_API_URL`, `CHATWOOT_API_KEY`, `N8N_API_URL`, `N8N_API_KEY`, `META_WHATSAPP_TOKEN`, `META_WABA_ID`, `GLPI_API_URL`, `GLPI_APP_TOKEN`, `GLPI_USER_TOKEN`, `ZABBIX_API_URL`, `ZABBIX_API_TOKEN`.
- **Opcionais de observabilidade**: `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN`, `SENTRY_ORG`, `SENTRY_PROJECT`, `SENTRY_AUTH_TOKEN`.

Notas importantes:

- O backend nao sobe em producao sem `JWT_PRIVATE_KEY` e `JWT_PUBLIC_KEY`; a validacao esta em [production.py](file:///c:/Users/yuri.menezes/Desktop/Projetos/papermoon/backend/core/settings/production.py#L15-L23).
- O ISR do CMS nao funciona sem `REVALIDATE_SECRET`; a rota retorna `503` em [route.ts](file:///c:/Users/yuri.menezes/Desktop/Projetos/papermoon/frontend/src/app/api/revalidate/route.ts#L15-L19).
- O faturamento real depende de `ASAAS_API_KEY`; o gateway usa a credencial diretamente em [asaas_adapter.py](file:///c:/Users/yuri.menezes/Desktop/Projetos/papermoon/backend/apps/billing/gateway/asaas_adapter.py#L13-L30).
- Chatwoot, n8n, GLPI, Zabbix e Meta WhatsApp entram em modo `stub` quando as credenciais nao existem; isso mantem o core da plataforma no ar, mas desabilita o provisionamento real dessas integracoes.
- Se nao for usar Sentry no corte, deixe `SENTRY_DSN` e `NEXT_PUBLIC_SENTRY_DSN` vazios em vez de manter placeholders `CHANGE-ME`.

### Chaves JWT RS256

`deploy.sh` gera o par de chaves automaticamente: antes das migrations, ele verifica se
`JWT_PRIVATE_KEY`/`JWT_PUBLIC_KEY` estão vazias em `.env.production` e, se estiverem, roda
`manage.py generate_jwt_keys` num container efêmero e grava o resultado direto no arquivo.
Nenhuma ação manual é necessária no primeiro deploy.

Para rotacionar as chaves manualmente (ex: suspeita de comprometimento):

```bash
make prod-generate-jwt
# Copiar JWT_PRIVATE_KEY e JWT_PUBLIC_KEY para .env.production e reiniciar:
docker compose -f docker-compose.prod.yml up -d --force-recreate django-api celery-worker celery-beat
```

---

## 4. Build e Start

```bash
cd /opt/papermoon

# Build das imagens de produção (usa Dockerfile.prod para o backend)
docker compose -f docker-compose.prod.yml build

# Subir todos os serviços
docker compose -f docker-compose.prod.yml up -d

# Aplicar migrations
docker compose -f docker-compose.prod.yml exec django-api python manage.py migrate --noinput

# Criar superusuário (primeiro deploy)
docker compose -f docker-compose.prod.yml exec django-api python manage.py createsuperuser

# ou simplesmente:
make prod-deploy
```

---

## 5. Conectar os Containers à Rede do Tunnel

Após o `docker compose up -d`, o Compose conecta `django-api` e `nextjs` automaticamente na rede externa `papermoon-network`, desde que ela exista no host. Verifique:

```bash
docker network inspect papermoon-network --format '{{range .Containers}}{{.Name}} {{end}}'
# Deve mostrar: cloudflared papermoon-api papermoon-web
```

Se `django-api` ou `nextjs` não aparecerem:

```bash
docker network connect papermoon-network papermoon-api
docker network connect papermoon-network papermoon-web
```

---

## 6. Smoke Tests

```bash
# Via Cloudflare (HTTPS externo) — o host de webhook aponta direto para o django-api
curl https://webhooks.papermoon.example.com/health/
# Esperado: {"success": true, "data": {"status": "ok", "db": "ok", "redis": "ok"}, "error": null}

curl -I https://app.papermoon.example.com/
# Esperado: HTTP/2 200

# Verificar que o tunnel recebe os headers corretos
curl -H "X-Forwarded-Proto: https" http://localhost:8000/health/
# (acesso direto ao container para debug — use docker exec)
```

---

## 7. Webhook Asaas

Registrar no painel Asaas:

```
URL: https://webhooks.papermoon.example.com/api/v1/webhooks/asaas/
```

Token: o mesmo valor de `ASAAS_WEBHOOK_TOKEN` no `.env.production`.

Eventos: `PAYMENT_CONFIRMED`, `PAYMENT_RECEIVED`, `PAYMENT_OVERDUE`, `PAYMENT_DELETED`.

---

## 8. Monitoramento

```bash
# Logs em tempo real
make prod-logs

# Status dos containers
docker compose -f docker-compose.prod.yml ps

# Celery
docker compose -f docker-compose.prod.yml exec celery-worker \
  celery -A core.celery_app inspect active

# Verificar rede
docker network inspect papermoon-network
```

---

## 9. Atualizações

```bash
cd /opt/papermoon
git pull origin main

# Rebuild apenas das imagens alteradas
docker compose -f docker-compose.prod.yml build django-api celery-worker celery-beat nextjs

# Aplicar migrations e reiniciar (zero-downtime para workers e nextjs)
docker compose -f docker-compose.prod.yml exec django-api python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml up -d --no-deps django-api celery-worker celery-beat nextjs
```

> `--no-deps` garante que `postgres` e `redis` não são reiniciados enquanto a aplicação atualiza.

---

## 10. Backup do Banco

```bash
export $(grep -E '^(POSTGRES_DB|POSTGRES_USER)=' .env.production | xargs)
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_$(date +%Y%m%d).sql
```

Cron diário (2h da manhã):

```
0 2 * * * cd /opt/papermoon && export $$(grep -E '^(POSTGRES_DB|POSTGRES_USER)=' .env.production | xargs) && docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres pg_dump -U "$$POSTGRES_USER" "$$POSTGRES_DB" > /backups/papermoon_$$(date +\%Y\%m\%d).sql
```

> Para concluir a troca dos identificadores de banco/usuario legados, siga o runbook
> [db-identifier-migration.md](file:///c:/Users/yuri.menezes/Desktop/Projetos/papermoon/docs/db-identifier-migration.md).

---

## Rollback

```bash
git checkout <commit-sha>
docker compose -f docker-compose.prod.yml build django-api celery-worker celery-beat nextjs
docker compose -f docker-compose.prod.yml exec django-api python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml up -d --no-deps django-api celery-worker celery-beat nextjs
```

Reverter migration:

```bash
docker compose -f docker-compose.prod.yml exec django-api \
  python manage.py migrate <app_name> <migration_anterior>
```

---

## Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| `django-api` sai imediatamente | `.env.production` com variável faltando | `docker compose -f docker-compose.prod.yml logs django-api` |
| 502 no Cloudflare | Container `django-api` ou `nextjs` não está up | `docker compose -f docker-compose.prod.yml ps` |
| Cookies não marcados como Secure | `X-Forwarded-Proto` não chegando no Django | Verificar logs cloudflared; confirmar `SECURE_PROXY_SSL_HEADER` em `production.py` |
| Tunnel não resolve `django-api` | cloudflared não está em `papermoon-network` | `docker network connect papermoon-network <cloudflared-container>` |
| Webhook retorna 403 | `ASAAS_WEBHOOK_TOKEN` divergente | Conferir token no `.env.production` vs painel Asaas |
| Celery tasks paradas | `celery-worker` ou `celery-beat` down | `docker compose -f docker-compose.prod.yml up -d celery-worker celery-beat` |
| Redis `NOAUTH` | `REDIS_PASSWORD` não definido no `REDIS_URL` | Confirmar que `REDIS_URL=redis://:SENHA@redis:6379/0` |
