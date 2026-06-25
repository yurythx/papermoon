# Checklist Final de Deploy — PaperMoon

Checklist operacional para preparar, executar e validar o deploy de produção.

> Este checklist complementa `docs/deployment.md`. Use este arquivo como roteiro de alto nível
> e o guia de deploy como referência detalhada.

---

## 1. Go / No-Go

- [ ] Janela de manutenção aprovada.
- [ ] Responsável técnico definido para executar o deploy.
- [ ] Responsável funcional definido para validar login, dashboard, faturamento e CMS.
- [ ] Backup recente do banco confirmado.
- [ ] Plano de rollback conhecido pela equipe.

---

## 2. Infraestrutura Base

- [ ] Servidor com Docker Engine 24+ e Docker Compose v2 instalados.
- [ ] `cloudflared` já está rodando como container no servidor.
- [ ] Rede externa `papermoon-network` criada (`make tunnel-network`).
- [ ] `cloudflared` conectado na rede `papermoon-network` (`make tunnel-connect`).
- [ ] DNS configurado no Cloudflare:
  - [ ] `app.papermoon.cloud` → Tunnel → `nextjs:3000`
  - [ ] `webhooks.papermoon.cloud` → Tunnel → `django-api:8000`

```bash
make tunnel-network
make tunnel-connect
docker network inspect papermoon-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

---

## 3. Segredos e Variáveis

> O `setup.sh` gera automaticamente todos os segredos criptográficos.
> Execute `sudo bash setup.sh` para o primeiro deploy e pule para a seção 4.

- [ ] `.env.production` existe na raiz do projeto.

Obrigatórias para subir a aplicação:

- [ ] `SECRET_KEY` preenchida (gerada pelo `setup.sh`).
- [ ] `POSTGRES_PASSWORD` preenchida (gerada pelo `setup.sh`).
- [ ] `REDIS_PASSWORD` preenchida (gerada pelo `setup.sh`).
- [ ] `DATABASE_URL` confere com `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD`.
- [ ] `REDIS_URL` confere com `REDIS_PASSWORD`.
- [ ] `REVALIDATE_SECRET` preenchida (gerada pelo `setup.sh`).
- [ ] `ALLOWED_HOSTS` aponta para `app.papermoon.cloud,webhooks.papermoon.cloud,django-api`.
- [ ] `CORS_ALLOWED_ORIGINS` = `https://app.papermoon.cloud`.
- [ ] `FRONTEND_URL` = `https://app.papermoon.cloud`.
- [ ] `JWT_PRIVATE_KEY` e `JWT_PUBLIC_KEY` vazios ou preenchidos — o `deploy.sh` gera se vazios.
- [ ] `FLOWER_USER` e `FLOWER_PASSWORD` preenchidos (gerados pelo `setup.sh`).

Obrigatórias para operação comercial:

- [ ] `ASAAS_API_KEY` é a chave real de produção (começa com `$aact_`).
- [ ] `ASAAS_WEBHOOK_TOKEN` confere com o token configurado no painel do Asaas.
- [ ] SMTP configurado (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`).
- [ ] `DEFAULT_FROM_EMAIL` usa o remetente final da operação.
- [ ] `ADMIN_NOTIFICATION_EMAIL` aponta para o e-mail que recebe alertas de novos cadastros.

Opcionais com degradação controlada:

- [ ] `CHATWOOT_API_URL` e `CHATWOOT_API_KEY` preenchidos, se Chatwoot estiver em uso.
- [ ] `N8N_API_URL` e `N8N_API_KEY` preenchidos, se n8n estiver em uso.
- [ ] `META_WHATSAPP_TOKEN` e `META_WABA_ID` preenchidos, se Meta WhatsApp estiver em uso.
- [ ] `GLPI_*`, `ZABBIX_*`, `TRUENAS_*`, `RUSTDESK_*` preenchidos conforme o ambiente.

Observabilidade:

- [ ] `SENTRY_DSN` e `NEXT_PUBLIC_SENTRY_DSN` configurados, ou deixados vazios para desabilitar.
- [ ] Nenhum valor `CHANGE-ME` restante nas integrações efetivamente usadas.

---

## 4. Preparação do Código

- [ ] Repositório clonado/atualizado em `/opt/papermoon`.
- [ ] Branch `main` atualizada.

```bash
git clone https://github.com/yurythx/papermoon.git /opt/papermoon
cd /opt/papermoon
git pull origin main
```

---

## 5. Backup Antes do Corte

- [ ] Backup lógico executado imediatamente antes do deploy.
- [ ] Arquivo de backup gerado com sucesso.
- [ ] Espaço em disco validado.

```bash
cd /opt/papermoon
make prod-backup
make prod-backup-list
```

---

## 6. Deploy

**Primeiro deploy — VPS zerada:**

```bash
sudo bash setup.sh
```

**Deploy subsequente — atualização:**

```bash
make prod-deploy
# ou: bash deploy.sh
```

O `deploy.sh` executa automaticamente:
1. `git pull origin main`
2. Build das imagens (`docker compose build --parallel`)
3. Geração de chaves JWT RS256 (se ausentes)
4. Sobe postgres + redis, aguarda health check
5. `python manage.py migrate --noinput`
6. `python manage.py collectstatic --noinput --clear`
7. `python manage.py check --deploy`
8. `docker compose up -d --remove-orphans`
9. Health check com retry (15 tentativas × 8s)
10. Rollback automático em caso de falha

- [ ] Build das imagens concluído sem erro.
- [ ] Migrations aplicadas com sucesso.
- [ ] Health check retornou `db=ok, redis=ok`.
- [ ] `django-api` e `nextjs` aparecem na rede `papermoon-network`.
- [ ] Superusuário criado: `make prod-superuser`.

```bash
make prod-ps
docker network inspect papermoon-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

---

## 7. Webhooks e Integrações

- [ ] Webhook do Asaas cadastrado com a URL final:
  `https://webhooks.papermoon.cloud/api/v1/webhooks/asaas/`
- [ ] Token do webhook confere com `ASAAS_WEBHOOK_TOKEN` no `.env.production`.
- [ ] Chatwoot validado, se estiver em uso.
- [ ] n8n validado, se estiver em uso.

---

## 8. Smoke Test Pós-Deploy

- [ ] Health check retorna `ok`.
- [ ] Home pública responde `200`.
- [ ] Login funciona.
- [ ] Dashboard do cliente abre.
- [ ] Backoffice abre.
- [ ] Faturamento lista dados sem erro.
- [ ] Reset de senha envia e-mail.
- [ ] Se CMS: revalidação funciona.
- [ ] Workers processando fila normalmente.

```bash
curl https://webhooks.papermoon.cloud/health/
curl -I https://app.papermoon.cloud/
make prod-health
make prod-logs
```

---

## 9. Observabilidade e Operação

- [ ] Logs sem erro crítico recorrente (`make prod-logs`).
- [ ] Healthchecks estão `healthy` (`make prod-ps`).
- [ ] Cron de backup instalado (feito automaticamente pelo `setup.sh`).
- [ ] Responsável pelo acompanhamento das primeiras horas definido.

Opcional mas recomendado:

- [ ] Sentry habilitado.
- [ ] Flower acessível internamente (`https://app.papermoon.cloud/flower/` ou port forward).
- [ ] Checklist de rotação de segredos definida.

---

## 10. Rollback

- [ ] Commit anterior conhecido.
- [ ] Backup imediatamente anterior localizado.

O `deploy.sh` faz rollback automático se o health check falhar. Para rollback manual:

```bash
cd /opt/papermoon
git checkout <commit-anterior>
bash deploy.sh --skip-pull
```

---

## 11. Fechamento

- [ ] Deploy comunicado como concluído.
- [ ] Evidências salvas: logs, horário do corte, versão implantada, resultado do smoke test.
- [ ] Pendências pós-deploy registradas para a próxima janela.
