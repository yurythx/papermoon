# Deployment Guide — PaperMoon

Guia de deploy para produção e para testes locais do stack de produção.

> Antes do corte, percorra também a checklist operacional em
> [production-deploy-checklist.md](checklists/production-deploy-checklist.md).

> **Arquitetura de rede:** Cloudflare fica na frente como proxy/TLS (`papermoon.cloud` resolve
> pros IPs anycast da Cloudflare — confirmado via DNS). Não há Nginx/Caddy/Let's Encrypt neste
> host. **Diferença confirmada em relação ao desenho original abaixo:** o host onde este
> `docker-compose.prod.yml` roda (LXC, ver [[papermoon-infra-topology]]) **não** tem um container
> `cloudflared` local nem participa de `papermoon-network` com ele — `docker network inspect
> papermoon-network` está vazio e `docker ps` não mostra `cloudflared` neste host. As portas
> `3000` (nextjs) e `8000` (django-api) estão expostas direto em `0.0.0.0` neste host
> (`192.168.1.102`), então o ponto de entrada real (provavelmente uma LXC de tunnel separada, no
> mesmo padrão das outras LXCs dedicadas do ambiente) fica fora do que este guia consegue
> documentar sem acesso a ela. **Domínio real em produção é `papermoon.cloud` (sem `app.`
> prefixo)** — `ALLOWED_HOSTS`/`FRONTEND_URL`/`CORS_ALLOWED_ORIGINS` em `.env.production` já usam
> só `papermoon.cloud`. O desenho abaixo é o objetivo original de arquitetura; trate as seções que
> mencionam `app.papermoon.cloud`, `webhooks.papermoon.cloud` e "nenhuma porta exposta" como
> aspiracionais até alguém com acesso à LXC de tunnel confirmar/atualizar.

---

## Visão Geral da Arquitetura (desenho original — ver aviso acima)

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
- Cloudflared já rodando (instalado previamente) — **em produção, roda numa LXC separada**, não
  neste host (ver aviso no topo deste guia)
- Domínio configurado no Cloudflare: `papermoon.cloud` (app + webhook do Asaas no mesmo domínio,
  não em subdomínios separados)
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
git clone https://github.com/yurythx/papermoon.git /opt/docker/papermoon
cd /opt/docker/papermoon
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

> Em produção hoje isso **não está conectado** (ver aviso no topo do guia) — o tunnel roda numa
> LXC separada e alcança este host pela LAN, não por essa rede Docker. Os comandos abaixo só
> fazem sentido se o cloudflared rodar no mesmo host que este `docker-compose.prod.yml`.

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

## Configuração do Tunnel no Cloudflare Dashboard (desenho original — ver aviso no topo)

No painel da Cloudflare → **Zero Trust → Networks → Tunnels → seu tunnel → Configure**:

| Hostname | Serviço | Uso |
|---|---|---|
| `app.papermoon.cloud` | `http://nextjs:3000` | App principal — todo o tráfego de usuário |
| `webhooks.papermoon.cloud` | `http://django-api:8000` | Só o webhook do Asaas |

> Os nomes `django-api` e `nextjs` são service names do Docker Compose. Esse desenho só funciona
> se o cloudflared estiver na mesma rede `papermoon-network` — **confirmado que não é o caso em
> produção hoje** (ver aviso no topo do guia). Na prática, `papermoon.cloud` (sem subdomínio)
> resolve pra Cloudflare e chega neste host via a LAN em `192.168.1.102:3000`/`:8000` — a
> configuração real do tunnel/ingress fica numa LXC separada, fora do alcance deste repositório.

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

> `webhooks.papermoon.cloud` não existe mais (não resolve em DNS, e `ALLOWED_HOSTS` em
> `.env.production` só lista `papermoon.cloud` — um request com esse Host antigo tomaria
> `DisallowedHost` no Django mesmo que chegasse). A URL abaixo usa o domínio único real; ainda
> assim, **confirme no painel Asaas qual URL está de fato cadastrada** antes de assumir que bate
> com isto — a configuração do ingress que decide se `/api/v1/webhooks/asaas/` chega até o
> `django-api` fica fora deste repositório (ver aviso no topo do guia).

Registrar no painel Asaas:

```
URL: https://papermoon.cloud/api/v1/webhooks/asaas/
```

Token: o mesmo valor de `ASAAS_WEBHOOK_TOKEN` no `.env.production`.

Eventos: `PAYMENT_CONFIRMED`, `PAYMENT_RECEIVED`, `PAYMENT_OVERDUE`, `PAYMENT_DELETED`.

---

## Smoke Tests Pós-Deploy

```bash
# No próprio host (o /health/ público em papermoon.cloud/health/ é interceptado pelo Next.js,
# não chega no django-api — testar direto no container é mais confiável):
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T django-api \
  curl -sf -H 'Host: django-api' http://localhost:8000/health/
# Esperado: {"success":true,"data":{"status":"ok","db":"ok","redis":"ok"},"error":null}

curl -I https://papermoon.cloud/
# Esperado: HTTP/2 200

# Verificar containers da stack (rede interna do Compose, não papermoon-network — ver aviso
# no topo do guia sobre onde o cloudflared realmente está):
docker compose -f docker-compose.prod.yml --env-file .env.production ps
# Todos devem estar "Up" / "healthy"
```

---

## Atualizações (após primeiro deploy)

Deploy automático via GitHub Actions em todo push para `main`. Para deploy manual:

```bash
cd /opt/docker/papermoon
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
cd /opt/docker/papermoon
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
