# Checklist Final de Deploy — PaperMoon

Checklist objetiva para preparar, executar e validar o deploy de producao do ecossistema PaperMoon.

> Este checklist complementa `docs/deployment.md`. Use este arquivo como roteiro operacional de alto nivel e o guia de deploy como referencia detalhada de comandos.

---

## 1. Go / No-Go

- [ ] Janela de manutencao aprovada.
- [ ] Responsavel tecnico definido para executar o deploy.
- [ ] Responsavel funcional definido para validar login, dashboard, faturamento e CMS.
- [ ] Backup recente do banco confirmado.
- [ ] Plano de rollback conhecido pela equipe.

---

## 2. Infraestrutura Base

- [ ] Servidor com Docker Engine 24+ e Docker Compose v2 instalados.
- [ ] `cloudflared` ja esta rodando como container no servidor.
- [ ] Rede externa `papermoon-network` criada.
- [ ] `cloudflared` conectado na rede `papermoon-network`.
- [ ] DNS configurado no Cloudflare para:
- [ ] `app.<dominio>`
- [ ] `webhooks.<dominio>`

Comandos uteis:

```bash
docker network create papermoon-network
docker ps --filter "ancestor=cloudflare/cloudflared" --format "{{.Names}}"
docker network connect papermoon-network cloudflared
docker network inspect papermoon-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

---

## 3. Segredos e Variaveis

- [ ] `.env.production` existe na raiz do projeto.

Obrigatorias para subir a aplicacao:

- [ ] `SECRET_KEY` esta preenchida com valor forte.
- [ ] `POSTGRES_PASSWORD` esta preenchida com valor forte.
- [ ] `REDIS_PASSWORD` esta preenchida com valor forte.
- [ ] `DATABASE_URL` confere com `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD`.
- [ ] `REDIS_URL` confere com `REDIS_PASSWORD`.
- [ ] `REVALIDATE_SECRET` esta preenchida com valor forte.
- [ ] `ALLOWED_HOSTS` aponta para os dominios finais.
- [ ] `CORS_ALLOWED_ORIGINS` aponta para o frontend final.
- [ ] `FRONTEND_URL` aponta para o dominio final do app.
- [ ] `JWT_PRIVATE_KEY` e `JWT_PUBLIC_KEY` existem ou serao geradas pelo fluxo de deploy antes de subir o backend.

Obrigatorias para operacao comercial:

- [ ] `ASAAS_API_KEY` esta real e validada no ambiente de producao.
- [ ] `ASAAS_WEBHOOK_TOKEN` confere com o token configurado no painel do Asaas.
- [ ] SMTP real esta configurado para reset de senha, convites e notificacoes.
- [ ] `EMAIL_HOST_PASSWORD` esta preenchida com credencial valida.
- [ ] `DEFAULT_FROM_EMAIL` usa o remetente final da operacao.

Opcionais com degradacao controlada:

- [ ] `CHATWOOT_API_URL` e `CHATWOOT_API_KEY` preenchidos, se Chatwoot estiver em uso.
- [ ] `N8N_API_URL` e `N8N_API_KEY` preenchidos, se n8n estiver em uso.
- [ ] `META_WHATSAPP_TOKEN` e `META_WABA_ID` preenchidos, se Meta WhatsApp estiver em uso.
- [ ] `GLPI_API_URL`, `GLPI_APP_TOKEN` e `GLPI_USER_TOKEN` preenchidos, se GLPI estiver em uso.
- [ ] `ZABBIX_API_URL` e `ZABBIX_API_TOKEN` preenchidos, se Zabbix estiver em uso.

Observabilidade e acabamento:

- [ ] `SENTRY_DSN` e `NEXT_PUBLIC_SENTRY_DSN` configurados, se observabilidade estiver habilitada.
- [ ] `SENTRY_ORG`, `SENTRY_PROJECT` e `SENTRY_AUTH_TOKEN` configurados, se houver upload de sourcemaps/releases.
- [ ] Nenhum valor `CHANGE-ME` restante nas integracoes efetivamente usadas.
- [ ] Placeholders de Sentry foram substituidos por valores reais ou limpos para vazio.

Observacao importante:

- Se o banco de producao ainda usa identificadores legados `riisen`, isso e suportado temporariamente.
- Se quiser concluir a padronizacao para `papermoon`, execute depois o runbook `docs/db-identifier-migration.md`.

---

## 4. Preparacao do Codigo

- [ ] Repositorio clonado/atualizado em `/opt/papermoon`.
- [ ] Branch ou commit final do deploy definido.
- [ ] `docker-compose.prod.yml` revisado e compativel com o ambiente.
- [ ] `docs/deployment.md` revisado pela equipe responsavel.

Comandos uteis:

```bash
git clone https://github.com/your-org/papermoon.git /opt/papermoon
cd /opt/papermoon
git fetch --all --tags
git checkout <branch-ou-commit>
```

---

## 5. Backup Antes do Corte

- [ ] Backup logico executado imediatamente antes do deploy.
- [ ] Arquivo de backup gerado com sucesso.
- [ ] Espaco em disco validado para backup e rollback.

Comando sugerido:

```bash
cd /opt/papermoon
export $(grep -E '^(POSTGRES_DB|POSTGRES_USER)=' .env.production | xargs)
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 6. Deploy

- [ ] Build das imagens de producao concluido.
- [ ] Containers principais iniciados com sucesso.
- [ ] Migrations aplicadas com sucesso.
- [ ] Superusuario criado ou validado.
- [ ] `django-api` e `nextjs` aparecem na rede `papermoon-network`.

Comandos base:

```bash
cd /opt/papermoon
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec django-api python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml exec django-api python manage.py createsuperuser
docker network inspect papermoon-network --format '{{range .Containers}}{{.Name}} {{end}}'
```

---

## 7. Webhooks e Integracoes

- [ ] Webhook do Asaas cadastrado com a URL final.
- [ ] Token do webhook do Asaas confere com `.env.production`.
- [ ] Chatwoot validado, se estiver em uso.
- [ ] n8n validado, se estiver em uso.
- [ ] Integracoes GLPI/Zabbix/Meta revisadas, se estiverem habilitadas nesse ambiente.

Referencia:

```text
https://webhooks.<dominio>/api/v1/webhooks/asaas/
```

---

## 8. Smoke Test Pos-Deploy

- [ ] `health` do backend retorna `ok`.
- [ ] Home publica responde `200`.
- [ ] Login funciona.
- [ ] Dashboard do cliente abre.
- [ ] Backoffice abre.
- [ ] Faturamento abre e lista dados sem erro.
- [ ] Reset de senha envia e-mail.
- [ ] Revalidacao do CMS funciona.
- [ ] Se houver tasks assincronas: worker processa fila normalmente.

Comandos uteis:

```bash
curl -I https://app.<dominio>/
curl https://webhooks.<dominio>/health/
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=200 django-api
docker compose -f docker-compose.prod.yml logs --tail=200 nextjs
docker compose -f docker-compose.prod.yml exec celery-worker celery -A core.celery_app inspect active
```

---

## 9. Observabilidade e Operacao

- [ ] Logs dos containers sem erro critico recorrente.
- [ ] Healthchecks estao `healthy`.
- [ ] Monitoramento/alerta configurado ou ao menos previsto.
- [ ] Politica de backup definida e testada.
- [ ] Responsavel pelo acompanhamento das primeiras horas de producao definido.

Opcional, mas recomendado:

- [ ] Sentry habilitado.
- [ ] Flower exposto apenas internamente ou nem publicado em producao.
- [ ] Checklist de rotacao de segredos definida.

---

## 10. Rollback

- [ ] Commit anterior conhecido.
- [ ] Backup imediatamente anterior localizado.
- [ ] Procedimento de rollback ensaiado pela equipe.

Comandos base:

```bash
cd /opt/papermoon
git checkout <commit-anterior>
docker compose -f docker-compose.prod.yml build django-api celery-worker celery-beat nextjs
docker compose -f docker-compose.prod.yml exec django-api python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml up -d --no-deps django-api celery-worker celery-beat nextjs
```

Se o corte do banco ainda estiver em naming legado:

- [ ] Manter `riisen` como fallback ate a migracao definitiva.

Se o corte do banco ja tiver mudado para `papermoon`:

- [ ] Seguir o rollback descrito em `docs/db-identifier-migration.md`.

---

## 11. Fechamento

- [ ] Deploy comunicado como concluido.
- [ ] Evidencias salvas: logs, horario do corte, versao implantada e resultado do smoke test.
- [ ] Pendencias pos-deploy registradas para a proxima janela.
