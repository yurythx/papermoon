#!/usr/bin/env bash
#
# scripts/local-prod-setup.sh — Sobe o stack de produção localmente para testes.
#
# O que faz:
#   1. Verifica pré-requisitos (Docker, docker compose)
#   2. Gera .env.production local se não existir (domínio=localhost)
#   3. Cria a rede Docker papermoon-network se não existir
#   4. Roda deploy.sh --skip-pull (build + JWT + migrate + start + healthcheck)
#   5. Imprime URLs de acesso local
#
# Uso:
#   bash scripts/local-prod-setup.sh
#   make local-prod-setup
#
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$APP_DIR/.env.production"

G='\033[0;32m'; BG='\033[1;32m'; YE='\033[1;33m'; RE='\033[0;31m'; CY='\033[0;36m'; NC='\033[0m'
info()    { printf "${G}  ◈  ${NC}%s\n" "$*"; }
success() { printf "${BG}  ✓  ${NC}%s\n" "$*"; }
warn()    { printf "${YE}  ⚡ ${NC}%s\n" "$*"; }
die()     { printf "${RE}  ✗  ${NC}%s\n" "$*" >&2; exit 1; }

printf "${BG}\n"
printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
printf '  ║   PaperMoon — Setup de Produção Local                           ║\n'
printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
printf "${NC}\n"

# ── Pré-requisitos ────────────────────────────────────────────────────────────
info "Verificando pré-requisitos..."
command -v docker >/dev/null 2>&1        || die "Docker não encontrado. Instale Docker Desktop."
docker info >/dev/null 2>&1              || die "Docker daemon não está rodando. Inicie o Docker Desktop."
docker compose version >/dev/null 2>&1   || die "docker compose (plugin v2) não encontrado."
command -v python3 >/dev/null 2>&1       || die "python3 não encontrado."
command -v openssl >/dev/null 2>&1       || die "openssl não encontrado."
success "Docker $(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"

# ── Geradores ─────────────────────────────────────────────────────────────────
gen_pass() { openssl rand -base64 48 | tr -d '/+=\n' | head -c 32; }
gen_hex()  { openssl rand -hex 32; }
gen_b64()  { openssl rand -base64 32 | tr -d '\n='; }
gen_django_key() {
  python3 -c "
import random, string
chars = string.ascii_letters + string.digits + '!@#%^&*(-_=+)'
print(''.join(random.choice(chars) for _ in range(50)))
"
}

# ── .env.production ───────────────────────────────────────────────────────────
if [[ -f "$ENV_FILE" ]]; then
  warn ".env.production já existe — mantendo. Apague para regenerar."
else
  info "Gerando .env.production para teste local..."

  PG_PASS="$(gen_pass)"
  REDIS_PASS="$(gen_pass)"
  SECRET_KEY="$(gen_django_key)"
  ASAAS_WH="$(gen_hex)"
  REVALIDATE="$(gen_b64)"
  FLOWER_PASS="$(gen_pass)"

  {
    printf '# Gerado por local-prod-setup.sh — apenas para testes locais\n\n'

    printf 'POSTGRES_DB=papermoon\n'
    printf 'POSTGRES_USER=papermoon\n'
    printf 'POSTGRES_PASSWORD=%s\n' "$PG_PASS"
    printf 'DATABASE_URL=postgres://papermoon:%s@postgres:5432/papermoon\n\n' "$PG_PASS"

    printf 'REDIS_PASSWORD=%s\n' "$REDIS_PASS"
    printf 'REDIS_URL=redis://:%s@redis:6379/0\n\n' "$REDIS_PASS"

    printf 'SECRET_KEY=%s\n' "$SECRET_KEY"
    printf 'DEBUG=False\n'
    printf 'ALLOWED_HOSTS=localhost,127.0.0.1,django-api\n'
    printf 'CORS_ALLOWED_ORIGINS=http://localhost:3000\n\n'

    printf 'JWT_PRIVATE_KEY=\n'
    printf 'JWT_PUBLIC_KEY=\n\n'

    printf 'FRONTEND_URL=http://localhost:3000\n'
    printf 'NEXTJS_INTERNAL_URL=http://nextjs:3000\n'
    printf 'NEXT_PUBLIC_SITE_URL=http://localhost:3000\n\n'

    printf 'EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend\n'
    printf 'EMAIL_HOST=\n'
    printf 'EMAIL_PORT=587\n'
    printf 'EMAIL_USE_TLS=True\n'
    printf 'EMAIL_HOST_USER=\n'
    printf 'EMAIL_HOST_PASSWORD=\n'
    printf 'DEFAULT_FROM_EMAIL=PaperMoon <noreply@localhost>\n'
    printf 'ADMIN_NOTIFICATION_EMAIL=admin@localhost\n\n'

    printf 'ASAAS_API_KEY=\n'
    printf 'ASAAS_WEBHOOK_TOKEN=%s\n\n' "$ASAAS_WH"

    printf 'FLOWER_USER=admin\n'
    printf 'FLOWER_PASSWORD=%s\n\n' "$FLOWER_PASS"

    printf 'REVALIDATE_SECRET=%s\n\n' "$REVALIDATE"

    printf 'BACKUP_DIR=\n'
    printf 'DAILY_RETENTION=7\n'
    printf 'WEEKLY_RETENTION=28\n'
    printf 'MONTHLY_RETENTION=90\n'
    printf 'BACKUP_RCLONE_REMOTE=\n\n'

    printf 'SENTRY_DSN=\n'
    printf 'NEXT_PUBLIC_SENTRY_DSN=\n'
    printf 'SENTRY_ORG=\n'
    printf 'SENTRY_PROJECT=\n'
    printf 'SENTRY_AUTH_TOKEN=\n\n'

    printf 'CHATWOOT_API_URL=\nCHATWOOT_API_KEY=\n'
    printf 'N8N_API_URL=\nN8N_API_KEY=\n'
    printf 'META_WHATSAPP_TOKEN=\nMETA_WABA_ID=\n'
    printf 'GLPI_API_URL=\nGLPI_APP_TOKEN=\nGLPI_USER_TOKEN=\n'
    printf 'ZABBIX_API_URL=\nZABBIX_API_TOKEN=\n'
    printf 'TRUENAS_API_URL=\nTRUENAS_API_KEY=\nTRUENAS_POOL=data\n'
    printf 'RUSTDESK_API_URL=\nRUSTDESK_API_KEY=\n'
    printf 'WINDOWS_SERVER_WAC_URL=\nWINDOWS_SERVER_WAC_KEY=\n'
    printf 'SAMBA_API_URL=\nSAMBA_API_KEY=\n'
  } > "$ENV_FILE"

  success ".env.production gerado"

  printf "${CY}"
  printf '  ┌─────────────────────────────────────────────────────────────┐\n'
  printf '  │  Flower (monitoramento Celery)                               │\n'
  printf "  │  Usuário : admin                                             │\n"
  printf "  │  Senha   : %-51s│\n" "$FLOWER_PASS"
  printf '  └─────────────────────────────────────────────────────────────┘\n'
  printf "${NC}\n"
fi

# ── Rede Docker ───────────────────────────────────────────────────────────────
if docker network ls | grep -q papermoon-network; then
  warn "Rede papermoon-network já existe"
else
  docker network create papermoon-network
  success "Rede papermoon-network criada"
fi

# ── Deploy ────────────────────────────────────────────────────────────────────
info "Rodando deploy local (build + JWT + migrate + start)..."
cd "$APP_DIR"
bash deploy.sh --skip-pull

# ── Subir com portas expostas ─────────────────────────────────────────────────
info "Expondo portas para acesso local..."
docker compose \
  -f "$APP_DIR/docker-compose.prod.yml" \
  -f "$APP_DIR/docker-compose.prod.ports.yml" \
  --env-file "$ENV_FILE" \
  up -d 2>/dev/null || true

printf "\n${BG}"
printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
printf '  ║   STACK LOCAL RODANDO                                            ║\n'
printf '  ╠══════════════════════════════════════════════════════════════════╣\n'
printf '  ║   Frontend  →  http://localhost:3000                             ║\n'
printf '  ║   API       →  http://localhost:8000/api/v1/                     ║\n'
printf '  ║   Admin     →  http://localhost:8000/admin/                      ║\n'
printf '  ║   API Docs  →  http://localhost:8000/api/docs/                   ║\n'
printf '  ║   Flower    →  http://localhost:5555/flower/                     ║\n'
printf '  ║   Health    →  http://localhost:8000/health/                     ║\n'
printf '  ╠══════════════════════════════════════════════════════════════════╣\n'
printf '  ║   Para criar superusuário: make prod-superuser                   ║\n'
printf '  ║   Para ver logs         : make local-prod-logs                   ║\n'
printf '  ║   Para parar            : make local-prod-down                   ║\n'
printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
printf "${NC}\n"
