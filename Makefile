# ── PaperMoon ───────────────────────────────────────────────────────────────
# Requires: docker, docker compose, make
# Usage: make <target>

DC      := docker compose
EXEC    := $(DC) exec -T django-api
BACKEND := $(EXEC)

# Produção — sempre usa env-file para expandir variáveis no compose file
PDC     := docker compose -f docker-compose.prod.yml --env-file .env.production
PEXEC   := $(PDC) exec -T django-api

.PHONY: help dev up down watch build restart logs ps \
        shell migrate migrations superuser seed seed-flush \
        test test-v test-cov check lint fmt typecheck \
        install install-dev hooks pre-commit-run \
        generate-jwt-keys \
        frontend frontend-dev frontend-build frontend-test frontend-e2e \
        prod-up prod-down prod-build prod-deploy prod-deploy-skip-pull \
        prod-logs prod-ps prod-health prod-shell prod-superuser prod-generate-jwt \
        prod-backup prod-backup-list prod-restore \
        local-prod-setup local-prod-up local-prod-down local-prod-logs \
        tunnel-network tunnel-connect setup setup-backup-cron \
        clean

# ── Help ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  ── Docker ───────────────────────────────────"
	@echo "  dev            Sobe containers em foreground"
	@echo "  up             Sobe containers em background"
	@echo "  watch          Hot-reload: synca arquivos e reinicia Celery ao salvar"
	@echo "  down           Para e remove containers"
	@echo "  build          Rebuild das imagens sem cache"
	@echo "  restart        down + up"
	@echo "  logs           Tail logs (django-api, celery-worker, celery-beat)"
	@echo "  flower         Abre o Flower (monitoramento Celery) em http://localhost:5555"
	@echo "  ps             Status dos containers"
	@echo ""
	@echo "  ── Django ───────────────────────────────────"
	@echo "  shell          Django shell interativo"
	@echo "  migrate        Aplica todas as migrations"
	@echo "  migrations     Cria migrations pendentes"
	@echo "  superuser      Cria superusuário admin"
	@echo "  seed           Cria dados de demo (idempotente)"
	@echo "  seed-flush     Limpa banco e recria dados de demo"
	@echo ""
	@echo "  ── Qualidade ────────────────────────────────"
	@echo "  test           Roda suite completa (silencioso)"
	@echo "  test-v         Roda suite com saída verbosa"
	@echo "  test-cov       Testes + relatório de cobertura"
	@echo "  check          Django system check (erros de configuração)"
	@echo "  lint           Verifica estilo com ruff"
	@echo "  fmt            Formata código com ruff format"
	@echo "  typecheck      Verifica tipos com mypy"
	@echo "  pre-commit-run Roda todos os hooks pre-commit"
	@echo ""
	@echo "  ── Frontend ─────────────────────────────────"
	@echo "  frontend       npm install"
	@echo "  frontend-dev   npm run dev (porta 3000)"
	@echo "  frontend-build npm run build (typecheck + bundle)"
	@echo "  frontend-test  vitest run (151 testes unitários/integração)"
	@echo "  frontend-e2e   playwright test (requer servidor rodando)"
	@echo ""
	@echo "  ── Produção ─────────────────────────────────"
	@echo "  prod-deploy         Deploy com pull + build + health check + rollback"
	@echo "  prod-deploy-skip-pull  Deploy sem git pull (rebuild forçado)"
	@echo "  prod-build          Rebuild completo sem cache"
	@echo "  prod-up / prod-down Start/stop serviços de produção"
	@echo "  prod-logs           Logs em tempo real (todos os serviços)"
	@echo "  prod-ps             Status dos containers de produção"
	@echo "  prod-health         Verifica /health/ (db, redis, celery)"
	@echo "  prod-shell          Django shell interativo (produção)"
	@echo "  prod-superuser      Cria superusuário admin (produção)"
	@echo "  prod-generate-jwt   Gera chaves JWT RS256 para produção"
	@echo "  prod-backup         Executa backup manual do banco agora"
	@echo "  prod-backup-list    Lista todos os backups locais"
	@echo "  prod-restore FILE=  Restaura backup (ex: FILE=backups/daily/papermoon_….sql.gz)"
	@echo "  local-prod-setup    Setup automático do stack prod localmente"
	@echo "  local-prod-up       Sobe stack prod local com portas expostas"
	@echo "  local-prod-down     Para stack prod local"
	@echo "  tunnel-network      Cria a rede Docker papermoon-network"
	@echo "  tunnel-connect      Conecta container cloudflared à rede"
	@echo "  setup               Configuração inicial da VPS (sudo)"
	@echo "  setup-backup-cron   Instala cron de backup diário (02:00)"
	@echo ""
	@echo "  ── Setup ────────────────────────────────────"
	@echo "  install        Instala dependências de produção"
	@echo "  install-dev    Instala dependências de dev"
	@echo "  hooks          Instala pre-commit hooks (ruff + mypy antes do commit)"
	@echo "  clean          Remove artefatos (.pyc, __pycache__)"
	@echo ""

# ── Docker ───────────────────────────────────────────────────────────────────
dev:
	$(DC) up

up:
	$(DC) up -d

watch:
	$(DC) watch

down:
	$(DC) down

build:
	$(DC) build --no-cache

restart: down up

logs:
	$(DC) logs -f django-api celery-worker celery-beat

flower:
	@echo "Flower disponível em http://localhost:5555"
	$(DC) up -d flower

ps:
	$(DC) ps

# ── Django ───────────────────────────────────────────────────────────────────
shell:
	$(DC) exec django-api python manage.py shell

migrate:
	$(BACKEND) python manage.py migrate

migrations:
	$(BACKEND) python manage.py makemigrations

superuser:
	$(DC) exec django-api python manage.py createsuperuser

seed:
	$(BACKEND) python manage.py seed

seed-flush:
	$(BACKEND) python manage.py seed --flush

# ── Qualidade ────────────────────────────────────────────────────────────────
test:
	$(BACKEND) python -m pytest tests/ -q --tb=short

test-v:
	$(BACKEND) python -m pytest tests/ -v

test-cov:
	$(BACKEND) python -m pytest tests/ -q --tb=short \
		--cov=. --cov-report=term-missing --cov-report=html:htmlcov
	@echo "Relatório em backend/htmlcov/index.html"

check:
	$(BACKEND) python manage.py check

lint:
	$(BACKEND) python -m ruff check .

fmt:
	$(BACKEND) python -m ruff format .

typecheck:
	$(BACKEND) python -m mypy . --config-file mypy.ini

pre-commit-run:
	$(BACKEND) pre-commit run --all-files

# ── Segurança ────────────────────────────────────────────────────────────────
generate-jwt-keys:
	@echo "Gerando par de chaves RSA-2048 para JWT RS256..."
	$(BACKEND) python manage.py generate_jwt_keys

# ── Setup ────────────────────────────────────────────────────────────────────
install:
	$(BACKEND) pip install -r requirements.txt

install-dev:
	$(BACKEND) pip install -r requirements.txt -r requirements-dev.txt

hooks:
	$(BACKEND) pre-commit install
	@echo "pre-commit hooks instalados. ruff + mypy vão rodar antes de cada commit."

# ── Frontend ─────────────────────────────────────────────────────────────────
frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm test

frontend-e2e:
	cd frontend && npx playwright test

frontend-e2e-install:
	cd frontend && npx playwright install chromium

frontend:
	cd frontend && npm install

# ── Produção ─────────────────────────────────────────────────────────────────
prod-up:
	$(PDC) up -d

prod-down:
	$(PDC) down

prod-build:
	$(PDC) build --no-cache

prod-deploy:
	@bash deploy.sh

prod-deploy-skip-pull:
	@bash deploy.sh --skip-pull

prod-logs:
	$(PDC) logs -f django-api celery-worker celery-beat nextjs

prod-ps:
	$(PDC) ps

prod-health:
	@$(PDC) exec -T django-api curl -sf -H 'Host: django-api' http://localhost:8000/health/ \
	  | python3 -m json.tool 2>/dev/null || echo "Django não está respondendo"

prod-shell:
	$(PDC) exec django-api python manage.py shell

prod-superuser:
	$(PDC) exec django-api python manage.py createsuperuser

prod-generate-jwt:
	$(PEXEC) python manage.py generate_jwt_keys

# ── Produção local (testa o stack prod na máquina de dev) ─────────────────────
local-prod-setup:
	@bash scripts/local-prod-setup.sh

local-prod-up:
	$(PDC) -f docker-compose.prod.ports.yml up -d

local-prod-down:
	$(PDC) -f docker-compose.prod.ports.yml down

local-prod-logs:
	$(PDC) -f docker-compose.prod.ports.yml logs -f django-api celery-worker nextjs

tunnel-network:
	docker network create papermoon-network 2>/dev/null || echo "Network papermoon-network already exists"

tunnel-connect:
	@read -p "Cloudflared container name: " name; \
	docker network connect papermoon-network $$name 2>/dev/null || true; \
	echo "Connected $$name to papermoon-network"

# Configuração inicial da VPS (executar como root/sudo na VPS)
setup:
	@sudo bash setup.sh

# ── Backup ────────────────────────────────────────────────────────────────────
prod-backup:
	@bash scripts/backup.sh

prod-backup-list:
	@echo "── Daily ──────────────────────────────────────────"
	@ls -lh backups/daily/*.sql.gz 2>/dev/null || echo "  (empty)"
	@echo "── Weekly ─────────────────────────────────────────"
	@ls -lh backups/weekly/*.sql.gz 2>/dev/null || echo "  (empty)"
	@echo "── Monthly ────────────────────────────────────────"
	@ls -lh backups/monthly/*.sql.gz 2>/dev/null || echo "  (empty)"

prod-restore:
	@test -n "$(FILE)" || (echo "Usage: make prod-restore FILE=backups/daily/papermoon_TIMESTAMP.sql.gz" && exit 1)
	@echo "WARNING: This will OVERWRITE the current database. Press Ctrl-C to abort..."
	@sleep 5
	gunzip -c "$(FILE)" | docker compose -f docker-compose.prod.yml --env-file .env.production \
		exec -T postgres psql -U "$$(grep POSTGRES_USER .env.production | cut -d= -f2)" \
		"$$(grep POSTGRES_DB .env.production | cut -d= -f2)"
	@echo "Restore complete."

setup-backup-cron:
	@bash scripts/setup-cron.sh

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true
	find backend -name ".coverage" -delete 2>/dev/null || true
