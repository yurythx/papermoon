# Deployment Guide — PaperMoon

Guia de deploy para produção e para testes locais do stack de produção.

> Antes do corte, percorra também a checklist operacional em
> [production-deploy-checklist.md](checklists/production-deploy-checklist.md).

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

- **Domínio principal**: `app.papermoon.cloud` → Next.js (BFF). Todas as chamadas de API do
  frontend passam por `/api/proxy/*`, que injeta o JWT e encaminha para `django-api` pela rede
  Docker. O backend nunca é exposto diretamente para esse tráfego.
- **Exceção: webhook do Asaas.** O BFF exige JWT de usuário — o Asaas não teria esse token.
  Por isso só `/api/v1/webhooks/asaas/` é exposto via `webhooks.papermoon.cloud` apontando
  direto para `django-api`, protegido pela validação do header `asaas-access-token`.
- **Cloudflare** termina TLS, aplica "Always Use HTTPS", gerencia certificados automaticamente.
- **Django** recebe HTTP puro vindo do tunnel. O header `X-Forwarded-Proto: https` injetado pelo
  cloudflared instrui Django a emitir cookies `Secure` corretamente.
- **Nenhuma porta** de `django-api` ou `nextjs` é exposta no host — acesso só pela rede do tunnel.

> O Compose usa `papermoon-network` como rede externa compartilhada com o cloudflared.

---

## Pré-requisitos

- Docker Engine 24+ e Docker Compose v2 no servidor
- Cloudflared já rodando como container (instalado previamente)
- Domínios configurados no Cloudflare:
  - `app.papermoon.cloud` → app principal
  - `webhooks.papermoon.cloud` → webhook Asaas (exclusivo)
- Conta Asaas com API key de produção
- Repositório em `github.com/yurythx/papermoon`

---

## Opção A — Primeiro deploy na VPS (setup completo)

O `setup.sh` executa tudo automaticamente em 9 passos: instala Docker, cria usuário,
**gera todos os segredos** (senhas de banco, Redis, Django, Flower, webhook token), pergunta
apenas o que não pode ser gerado (domínio, e-mail, SMTP, chave Asaas), configura firewall,
cria rede Docker, roda o primeiro deploy e instala o cron de backup.

```bash
# Na VPS, como root
git clone https://github.com/yurythx/papermoon.git /opt/papermoon
cd /opt/papermoon
sudo bash setup.sh
```

O script só vai te perguntar:

| Pergunta | Exemplo |
|---|---|
| Domínio base (sem https://) | `papermoon.cloud` |
| E-mail do administrador | `ops@papermoon.cloud` |
| Servidor SMTP (Enter para pular) | `smtp.sendgrid.net` |
| API Key do Asaas (Enter para pular) | `$aact_...` |
| Usuário do Flower | `admin` |

Ao final, o script exibe os 5 secrets para cadastrar no GitHub Actions.

---

## Opção B — Deploy subsequente (atualização)

Todo push para `main` dispara o CI/CD automaticamente via GitHub Actions (`.github/workflows/cd.yml`).
O `deploy.sh` na VPS executa: build → JWT → migrations → collectstatic → restart → health check,
com rollback automático se qualquer passo falhar.

```bash
# Manual, se precisar forçar sem aguardar CI:
make prod-deploy

# Ou direto:
bash deploy.sh

# Rebuild sem git pull (ex: mudança só no .env.production):
bash deploy.sh --skip-pull
```

---

## Opção C — Teste local do stack de produção

Para validar o stack prod na máquina de desenvolvimento antes de subir para a VPS:

```bash
make local-prod-setup
```

O script `scripts/local-prod-setup.sh` faz:
1. Gera `.env.production` local com valores de teste (domínio = `localhost`)
2. Cria a rede Docker `papermoon-network`
3. Roda `bash deploy.sh --skip-pull` (build + JWT + migrate + start)
4. Expõe portas via `docker-compose.prod.ports.yml`

Após subir:

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000/api/v1/ |
| Admin Django | http://localhost:8000/admin/ |
| API Docs (Swagger) | http://localhost:8000/api/docs/ |
| Flower (Celery) | http://localhost:5555/flower/ |
| Health check | http://localhost:8000/health/ |

```bash
make prod-superuser      # criar superusuário
make local-prod-logs     # ver logs
make local-prod-down     # parar tudo
```

---

## Configuração Manual da Rede Docker (se necessário)

```bash
# Criar rede (uma única vez por servidor)
make tunnel-network

# Verificar nome do container cloudflared
docker ps --filter "ancestor=cloudflare/cloudflared" --format "{{.Names}}"

# Conectar cloudflared à rede
make tunnel-connect     # interativo — pede o nome do container

# Verificar
docker network inspect papermoon-network --format '{{range .Containers}}{{.Name}} {{end}}'
# Deve mostrar: cloudflared
```

---

## Configuração do Tunnel no Cloudflare Dashboard

No painel da Cloudflare → **Zero Trust → Networks → Tunnels → seu tunnel → Configure**:

| Hostname | Serviço | Uso |
|---|---|---|
| `app.papermoon.cloud` | `http://nextjs:3000` | App principal — todo o tráfego de usuário |
| `webhooks.papermoon.cloud` | `http://django-api:8000` | Só o webhook do Asaas |

> Os nomes `django-api` e `nextjs` são service names do Docker Compose. O cloudflared os resolve
> porque está na mesma rede `papermoon-network`.

---

## Variáveis de Ambiente

O `setup.sh` gera automaticamente todos os segredos criptográficos. Os campos que precisam
de informação humana são documentados no [.env.production.example](../.env.production.example).

### Prioridade real das variáveis

- **Obrigatórias para subir**: `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL`,
  `REDIS_PASSWORD`, `REDIS_URL`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`,
  `REVALIDATE_SECRET`. JWT é gerado automaticamente pelo `deploy.sh`.
- **Obrigatórias para operação comercial**: `ASAAS_API_KEY`, `ASAAS_WEBHOOK_TOKEN`,
  `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
- **Opcionais com degradação controlada**: `CHATWOOT_*`, `N8N_*`, `META_*`, `GLPI_*`,
  `ZABBIX_*`, `TRUENAS_*`, `RUSTDESK_*` — entram em modo `stub` quando ausentes.
- **Opcionais de observabilidade**: `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN`.

### Chaves JWT RS256

`deploy.sh` detecta `JWT_PRIVATE_KEY`/`JWT_PUBLIC_KEY` vazias em `.env.production` e gera
o par RSA-2048 automaticamente antes das migrations. Nenhuma ação manual é necessária.

Para rotacionar (ex: suspeita de comprometimento):

```bash
make prod-generate-jwt
# Copiar as chaves geradas para .env.production e reiniciar:
make prod-up
```

---

## Comandos de Operação

Todos os comandos `make prod-*` usam `--env-file .env.production` automaticamente.

```bash
make prod-up             # sobe todos os serviços
make prod-down           # para todos os serviços
make prod-logs           # logs em tempo real (api, workers, nextjs)
make prod-ps             # status dos containers
make prod-health         # verifica /health/ (db, redis)
make prod-shell          # Django shell interativo
make prod-superuser      # cria superusuário admin
make prod-build          # rebuild completo sem cache
```

---

## Webhook Asaas

Registrar no painel Asaas:

```
URL: https://webhooks.papermoon.cloud/api/v1/webhooks/asaas/
```

Token: o mesmo valor de `ASAAS_WEBHOOK_TOKEN` no `.env.production`.

Eventos: `PAYMENT_CONFIRMED`, `PAYMENT_RECEIVED`, `PAYMENT_OVERDUE`, `PAYMENT_DELETED`.

---

## Smoke Tests Pós-Deploy

```bash
# Health check via Cloudflare (o hostname de webhook aponta direto para django-api)
curl https://webhooks.papermoon.cloud/health/
# Esperado: {"success":true,"data":{"status":"ok","db":"ok","redis":"ok"},"error":null}

curl -I https://app.papermoon.cloud/
# Esperado: HTTP/2 200

# Verificar rede
docker network inspect papermoon-network --format '{{range .Containers}}{{.Name}} {{end}}'
# Deve conter: cloudflared papermoon-api papermoon-web
```

---

## Atualizações (após primeiro deploy)

Deploy automático via GitHub Actions em todo push para `main`. Para deploy manual:

```bash
cd /opt/papermoon
bash deploy.sh           # pull + build + migrate + restart + health check
```

---

## Backup

```bash
make prod-backup          # executa agora
make prod-backup-list     # lista backups locais
make prod-restore FILE=backups/daily/papermoon_TIMESTAMP.sql.gz
```

Cron de backup diário às 02:00 é instalado automaticamente pelo `setup.sh`.

---

## Rollback

O `deploy.sh` faz rollback automático em caso de falha. Para rollback manual:

```bash
cd /opt/papermoon
git checkout <commit-anterior>
bash deploy.sh --skip-pull
```

---

## Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| `django-api` sai imediatamente | Variável faltando em `.env.production` | `make prod-logs` |
| 502 no Cloudflare | Container `django-api` ou `nextjs` não está up | `make prod-ps` |
| Cookies não marcados como Secure | `X-Forwarded-Proto` não chegando | Verificar logs cloudflared |
| Tunnel não resolve `django-api` | cloudflared não está em `papermoon-network` | `make tunnel-connect` |
| Webhook retorna 403 | `ASAAS_WEBHOOK_TOKEN` divergente | Conferir token vs painel Asaas |
| Celery tasks paradas | `celery-worker` ou `celery-beat` down | `make prod-up` |
| Redis `NOAUTH` | `REDIS_PASSWORD` não definido no `REDIS_URL` | Confirmar `REDIS_URL=redis://:SENHA@redis:6379/0` |
| Postgres sem senha | `--env-file .env.production` não passado | Usar `make prod-*` (já inclui) |
| Static files 404 | Build sem collectstatic | `make prod-build` (Dockerfile.prod coleta no build) |
