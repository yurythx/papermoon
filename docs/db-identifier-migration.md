# Database Identifier Migration — `riisen` -> `papermoon`

Runbook para migrar o identificador do banco e do usuario de producao de `riisen` para `papermoon`
sem renomear o cluster in-place. A estrategia recomendada e criar o novo role/database, restaurar um
dump consistente, validar a aplicacao e manter o banco antigo disponivel para rollback imediato.

## Quando usar

Use este runbook quando:

- o ambiente de producao ainda usa `POSTGRES_DB=riisen` e `POSTGRES_USER=riisen`;
- a aplicacao e a documentacao ja estao padronizadas para PaperMoon;
- voce quer concluir a migracao sem depender de rename destrutivo no banco ativo.

Nao use este runbook quando:

- o ambiente ainda nao tem backup recente validado;
- nao existe janela de manutencao aprovada;
- o volume do Postgres esta com problemas de espaco.

## Estrategia

Em vez de executar `ALTER DATABASE riisen RENAME TO papermoon` e `ALTER ROLE riisen RENAME TO papermoon`
em cima do banco ativo, o procedimento cria um novo role/database e faz restore do dump.

Vantagens:

- rollback simples, porque `riisen` permanece intacto;
- menor risco operacional;
- validacao controlada antes do corte final;
- facilita comparar o estado antigo e o novo lado a lado.

Trade-off:

- exige espaco temporario adicional para manter duas copias logicas durante a migracao.

## Pre-requisitos

- Janela de manutencao aprovada.
- Backup logico recente executado com `make prod-backup`.
- Acesso ao host onde roda `docker compose`.
- `.env.production` atualizado e conhecido.
- Espaco em disco suficiente para um dump completo + banco restaurado.

## 1. Descobrir identificadores atuais

No host de producao:

```bash
cd /opt/papermoon
export $(grep -E '^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD)=' .env.production | xargs)
printf 'DB atual: %s\nUsuario atual: %s\n' "$POSTGRES_DB" "$POSTGRES_USER"
```

Esperado hoje em ambientes legados:

```bash
DB atual: riisen
Usuario atual: riisen
```

## 2. Backup antes da mudanca

Execute o backup logico usando os identificadores atuais:

```bash
cd /opt/papermoon
make prod-backup
ls -lah backups/daily | tail
```

Opcionalmente valide o dump:

```bash
gzip -t backups/daily/papermoon_<db>_<timestamp>.sql.gz
```

## 3. Entrar em modo de manutencao

Pare os servicos da aplicacao para congelar novas escritas, mantendo `postgres` e `redis` ligados:

```bash
cd /opt/papermoon
docker compose -f docker-compose.prod.yml --env-file .env.production \
  stop nextjs django-api celery-worker celery-beat flower
```

## 4. Criar role e database `papermoon`

Use o usuario atual com privilegios administrativos para criar o novo role e o novo banco.

```bash
cd /opt/papermoon
export $(grep -E '^(POSTGRES_DB|POSTGRES_USER|POSTGRES_PASSWORD)=' .env.production | xargs)

docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  psql -U "$POSTGRES_USER" -d postgres <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'papermoon') THEN
    CREATE ROLE papermoon WITH LOGIN PASSWORD 'CHANGE-ME-PAPERMOON-DB-PASSWORD' SUPERUSER;
  END IF;
END $$;

SELECT 'CREATE DATABASE papermoon OWNER papermoon'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'papermoon')\gexec
SQL
```

Se voce nao quiser manter `SUPERUSER` no novo role, reduza os privilegios depois do corte:

```sql
ALTER ROLE papermoon NOSUPERUSER;
```

## 5. Restaurar o dump no novo banco

Restaure o dump mais recente para `papermoon`:

```bash
cd /opt/papermoon
LATEST_BACKUP=$(ls -t backups/daily/*.sql.gz | head -1)
gunzip -c "$LATEST_BACKUP" | docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec -T postgres psql -U papermoon -d papermoon
```

## 6. Validar o banco restaurado

Cheque rapidamente se tabelas e migrations apareceram:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  psql -U papermoon -d papermoon -c '\dt'

docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  psql -U papermoon -d papermoon -c 'SELECT count(*) FROM django_migrations;'
```

## 7. Atualizar `.env.production`

Somente depois do restore bem-sucedido, altere:

```env
POSTGRES_DB=papermoon
POSTGRES_USER=papermoon
POSTGRES_PASSWORD=<nova-senha-ou-mesma-senha>
DATABASE_URL=postgres://papermoon:<senha>@postgres:5432/papermoon
```

Se quiser reaproveitar a senha antiga no corte inicial, isso reduz variaveis durante a migracao.

## 8. Subir a aplicacao apontando para o novo banco

```bash
cd /opt/papermoon
docker compose -f docker-compose.prod.yml --env-file .env.production up -d postgres redis
docker compose -f docker-compose.prod.yml --env-file .env.production up -d django-api celery-worker celery-beat flower nextjs
```

## 9. Smoke tests apos o corte

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T django-api \
  curl -sf -H 'Host: django-api' http://localhost:8000/health/

curl -I https://app.papermoon.example.com/
```

Tambem valide:

- login administrativo;
- dashboard do cliente;
- revalidacao do CMS;
- filas Celery;
- webhook Asaas em homologacao, se existir ambiente espelho.

## 10. Rollback

Se qualquer validacao critica falhar:

1. pare os servicos da aplicacao;
2. restaure o `.env.production` anterior;
3. suba novamente a stack apontando para `riisen`.

Comandos:

```bash
cd /opt/papermoon
docker compose -f docker-compose.prod.yml --env-file .env.production \
  stop nextjs django-api celery-worker celery-beat flower

# restaurar .env.production anterior

docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

Como o banco `riisen` original nao foi renomeado nem sobrescrito, o rollback e imediato.

## 11. Limpeza posterior

Depois de alguns dias de operacao estavel com `papermoon`:

- remover o banco legado `riisen`;
- remover o role legado `riisen`;
- atualizar qualquer monitoramento ou backup externo ainda apontando para os nomes antigos.

Exemplo:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  psql -U papermoon -d postgres -c "DROP DATABASE riisen;"

docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  psql -U papermoon -d postgres -c "DROP ROLE riisen;"
```

So execute essa limpeza depois de confirmar que backups, cron, observabilidade e restore foram testados
com `papermoon`.
