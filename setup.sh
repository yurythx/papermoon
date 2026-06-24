#!/usr/bin/env bash
#
# setup.sh — Configuração inicial da VPS para o PaperMoon
#
# O que este script faz:
#   1. Atualiza o sistema e instala dependências base
#   2. Instala Docker + Docker Compose
#   3. Cria o usuário de aplicação "papermoon"
#   4. Gera .env.production automaticamente (pede apenas domínio, e-mail e API keys)
#   5. Configura firewall UFW
#   6. Cria rede Docker "papermoon-network"
#   7. Executa o primeiro deploy
#   8. Instala cron de backup diário às 02:00
#   9. Gera chave SSH ED25519 para GitHub Actions CD
#
# Uso:
#   sudo bash setup.sh
#
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# ── Cores ─────────────────────────────────────────────────────────────────────
G='\033[0;32m'; BG='\033[1;32m'; YE='\033[1;33m'; RE='\033[0;31m'; CY='\033[0;36m'; NC='\033[0m'

info()    { printf "${G}  ◈  ${NC}%s\n"        "$*"; }
success() { printf "${BG}  ✓  ${NC}%s\n"        "$*"; }
warn()    { printf "${YE}  ⚡ ${NC}%s\n"         "$*"; }
error()   { printf "${RE}  ✗  ${NC}%s\n" "$*" >&2; }
die()     { error "$*"; exit 1; }
ask()     { printf "${CY}  → ${NC}%s " "$*"; }
blank()   { printf "\n"; }

_STEP=0
step() {
  _STEP=$(( _STEP + 1 ))
  blank
  printf "${BG}  ┌──────────────────────────────────────────────────────────────┐\n"
  printf "  │  [%02d/09]  %-53s│\n" "$_STEP" "$*"
  printf "  └──────────────────────────────────────────────────────────────┘${NC}\n"
}

# ── Verificação de root ───────────────────────────────────────────────────────
[[ $EUID -ne 0 ]] && die "Execute como root: sudo bash setup.sh"

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="${APP_USER:-papermoon}"

# ── Banner ────────────────────────────────────────────────────────────────────
printf "${BG}"
printf '\n  ╔══════════════════════════════════════════════════════════════════╗\n'
printf   '  ║                                                                  ║\n'
printf   '  ║   PaperMoon — Setup de Produção                                  ║\n'
printf   '  ║                                                                  ║\n'
printf   "  ║   dir: %-58s║\n" "$APP_DIR"
printf   "  ║   OS : %-58s║\n" "$(lsb_release -ds 2>/dev/null || uname -sr)"
printf   '  ║                                                                  ║\n'
printf   '  ╚══════════════════════════════════════════════════════════════════╝\n'
printf "${NC}\n"

# ── Geradores de segredos ─────────────────────────────────────────────────────
# Gera senha sem caracteres especiais que quebram URLs (sem / + = @ : )
gen_pass()       { openssl rand -base64 48 | tr -d '/+=\n' | head -c 32; }
gen_hex()        { openssl rand -hex 32; }
gen_b64()        { openssl rand -base64 32 | tr -d '\n='; }

gen_django_key() {
  python3 -c "
import random, string
chars = string.ascii_letters + string.digits + '!@#%^&*(-_=+)'
print(''.join(random.choice(chars) for _ in range(50)))
"
}

# ── Passo 1: Sistema ──────────────────────────────────────────────────────────
step "Atualizando sistema e instalando dependências"

info "Atualizando lista de pacotes..."
apt-get update -q

info "Aplicando atualizações (pode levar alguns minutos)..."
apt-get upgrade -y \
  -o Dpkg::Options::="--force-confdef" \
  -o Dpkg::Options::="--force-confold" \
  -q

info "Instalando dependências base..."
apt-get install -y -q \
  ca-certificates gnupg lsb-release curl git unzip jq htop logrotate ufw python3

success "Sistema atualizado"

# ── Passo 2: Docker ───────────────────────────────────────────────────────────
step "Docker + Docker Compose"

if command -v docker >/dev/null 2>&1; then
  warn "Docker já instalado: $(docker --version)"
else
  info "Adicionando repositório oficial do Docker..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list

  apt-get update -q
  info "Instalando Docker Engine..."
  apt-get install -y -q \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
  success "Docker instalado: $(docker --version)"
fi

if ! docker compose version >/dev/null 2>&1; then
  die "docker compose (plugin v2) não encontrado. Verifique a instalação."
fi
success "Docker Compose: $(docker compose version)"

# ── Passo 3: Usuário da aplicação ─────────────────────────────────────────────
step "Usuário de aplicação: $APP_USER"

if id "$APP_USER" &>/dev/null; then
  warn "Usuário $APP_USER já existe"
else
  useradd -r -m -s /bin/bash -d "/home/$APP_USER" "$APP_USER"
  success "Usuário $APP_USER criado"
fi
usermod -aG docker "$APP_USER"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
success "Permissões ajustadas ($APP_USER adicionado ao grupo docker)"

# ── Passo 4: Gerar .env.production ───────────────────────────────────────────
step "Gerando .env.production"

ENV_FILE="$APP_DIR/.env.production"

if [[ -f "$ENV_FILE" ]]; then
  warn ".env.production já existe — mantendo arquivo atual."
  warn "Para regenerar: rm .env.production && sudo bash setup.sh"
else
  # ── Geração automática de segredos ──────────────────────────────────────────
  info "Gerando segredos automaticamente..."
  PG_PASS="$(gen_pass)"
  REDIS_PASS="$(gen_pass)"
  SECRET_KEY="$(gen_django_key)"
  ASAAS_WH_TOKEN="$(gen_hex)"
  REVALIDATE_SECRET="$(gen_b64)"
  FLOWER_PASS="$(gen_pass)"

  # ── Perguntas ao usuário ─────────────────────────────────────────────────────
  blank
  printf "${BG}  ┌──────────────────────────────────────────────────────────────┐\n"
  printf   '  │  Preciso de algumas informações para configurar o sistema.       │\n'
  printf   '  │  Responda cada pergunta. Pressione Enter para pular opcionais.   │\n'
  printf   '  └──────────────────────────────────────────────────────────────┘\n'
  printf "${NC}\n"

  # Domínio
  ask "Domínio base (ex: papermoon.com.br, SEM https://):"
  read -r DOMAIN
  [[ -z "$DOMAIN" ]] && die "Domínio é obrigatório."
  DOMAIN="${DOMAIN#https://}"  # Remove https:// se o usuário digitou

  # E-mail admin
  ask "E-mail do administrador (recebe notificações de cadastros):"
  read -r ADMIN_EMAIL
  [[ -z "$ADMIN_EMAIL" ]] && die "E-mail do administrador é obrigatório."

  # SMTP
  blank
  info "Configuração de e-mail (SMTP) — pressione Enter para pular e configurar depois."
  ask "Servidor SMTP (ex: smtp.sendgrid.net, smtp.gmail.com) [Enter para pular]:"
  read -r SMTP_HOST
  SMTP_USER="" SMTP_PASS="" SMTP_PORT="587"
  if [[ -n "$SMTP_HOST" ]]; then
    ask "Porta SMTP [587]:"
    read -r SMTP_PORT_INPUT
    SMTP_PORT="${SMTP_PORT_INPUT:-587}"
    ask "Usuário SMTP (para SendGrid: 'apikey'):"
    read -r SMTP_USER
    ask "Senha/API Key SMTP:"
    read -rs SMTP_PASS
    blank
  fi

  # Asaas
  blank
  info "Asaas (gateway de pagamento) — pressione Enter para configurar depois."
  ask "API Key do Asaas (produção, começa com \$aact_...) [Enter para pular]:"
  read -rs ASAAS_KEY
  blank

  # Flower (monitoramento Celery)
  ask "Usuário do painel Flower (monitoramento) [admin]:"
  read -r FLOWER_USER_INPUT
  FLOWER_USER="${FLOWER_USER_INPUT:-admin}"

  # ── Escrita do .env.production ───────────────────────────────────────────────
  info "Escrevendo .env.production..."

  {
    printf '# Gerado automaticamente por setup.sh em %s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
    printf '# NÃO commite este arquivo no git.\n\n'

    printf '# ── Banco de dados ──────────────────────────────────────────────────\n'
    printf 'POSTGRES_DB=papermoon\n'
    printf 'POSTGRES_USER=papermoon\n'
    printf 'POSTGRES_PASSWORD=%s\n' "$PG_PASS"
    printf 'DATABASE_URL=postgres://papermoon:%s@postgres:5432/papermoon\n\n' "$PG_PASS"

    printf '# ── Redis ───────────────────────────────────────────────────────────\n'
    printf 'REDIS_PASSWORD=%s\n' "$REDIS_PASS"
    printf 'REDIS_URL=redis://:%s@redis:6379/0\n\n' "$REDIS_PASS"

    printf '# ── Django ──────────────────────────────────────────────────────────\n'
    printf 'SECRET_KEY=%s\n' "$SECRET_KEY"
    printf 'DEBUG=False\n'
    printf 'ALLOWED_HOSTS=app.%s,webhooks.%s,django-api\n' "$DOMAIN" "$DOMAIN"
    printf 'CORS_ALLOWED_ORIGINS=https://app.%s\n\n' "$DOMAIN"

    printf '# ── JWT RS256 (gerado automaticamente pelo deploy.sh) ───────────────\n'
    printf 'JWT_PRIVATE_KEY=\n'
    printf 'JWT_PUBLIC_KEY=\n\n'

    printf '# ── URLs ────────────────────────────────────────────────────────────\n'
    printf 'FRONTEND_URL=https://app.%s\n' "$DOMAIN"
    printf 'NEXTJS_INTERNAL_URL=http://nextjs:3000\n'
    printf 'NEXT_PUBLIC_SITE_URL=https://app.%s\n\n' "$DOMAIN"

    printf '# ── E-mail / SMTP ───────────────────────────────────────────────────\n'
    printf 'EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n'
    printf 'EMAIL_HOST=%s\n' "${SMTP_HOST:-smtp.sendgrid.net}"
    printf 'EMAIL_PORT=%s\n' "$SMTP_PORT"
    printf 'EMAIL_USE_TLS=True\n'
    printf 'EMAIL_HOST_USER=%s\n' "${SMTP_USER:-apikey}"
    printf 'EMAIL_HOST_PASSWORD=%s\n' "${SMTP_PASS:-}"
    printf 'DEFAULT_FROM_EMAIL=PaperMoon <noreply@%s>\n' "$DOMAIN"
    printf 'ADMIN_NOTIFICATION_EMAIL=%s\n\n' "$ADMIN_EMAIL"

    printf '# ── Asaas (gateway de pagamento) ────────────────────────────────────\n'
    printf 'ASAAS_API_KEY=%s\n' "${ASAAS_KEY:-}"
    printf 'ASAAS_WEBHOOK_TOKEN=%s\n\n' "$ASAAS_WH_TOKEN"

    printf '# ── Flower (monitoramento Celery) ───────────────────────────────────\n'
    printf 'FLOWER_USER=%s\n' "$FLOWER_USER"
    printf 'FLOWER_PASSWORD=%s\n\n' "$FLOWER_PASS"

    printf '# ── CMS / ISR revalidation ───────────────────────────────────────────\n'
    printf 'REVALIDATE_SECRET=%s\n\n' "$REVALIDATE_SECRET"

    printf '# ── Backup ───────────────────────────────────────────────────────────\n'
    printf 'BACKUP_DIR=\n'
    printf 'DAILY_RETENTION=7\n'
    printf 'WEEKLY_RETENTION=28\n'
    printf 'MONTHLY_RETENTION=90\n'
    printf 'BACKUP_RCLONE_REMOTE=\n\n'

    printf '# ── Sentry (opcional — deixe em branco para desativar) ───────────────\n'
    printf 'SENTRY_DSN=\n'
    printf 'NEXT_PUBLIC_SENTRY_DSN=\n'
    printf 'SENTRY_ORG=\n'
    printf 'SENTRY_PROJECT=\n'
    printf 'SENTRY_AUTH_TOKEN=\n\n'

    printf '# ── Integrações externas (opcional) ─────────────────────────────────\n'
    printf 'CHATWOOT_API_URL=https://app.chatwoot.com\n'
    printf 'CHATWOOT_API_KEY=\n'
    printf 'N8N_API_URL=\n'
    printf 'N8N_API_KEY=\n'
    printf 'META_WHATSAPP_TOKEN=\n'
    printf 'META_WABA_ID=\n'
    printf 'GLPI_API_URL=\n'
    printf 'GLPI_APP_TOKEN=\n'
    printf 'GLPI_USER_TOKEN=\n'
    printf 'ZABBIX_API_URL=\n'
    printf 'ZABBIX_API_TOKEN=\n'
    printf 'TRUENAS_API_URL=\n'
    printf 'TRUENAS_API_KEY=\n'
    printf 'TRUENAS_POOL=data\n'
    printf 'RUSTDESK_API_URL=\n'
    printf 'RUSTDESK_API_KEY=\n'
    printf 'WINDOWS_SERVER_WAC_URL=\n'
    printf 'WINDOWS_SERVER_WAC_KEY=\n'
    printf 'SAMBA_API_URL=\n'
    printf 'SAMBA_API_KEY=\n'
  } > "$ENV_FILE"

  chown "$APP_USER:$APP_USER" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  success ".env.production criado"

  # ── Resumo do que foi gerado ──────────────────────────────────────────────
  blank
  printf "${BG}"
  printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
  printf '  ║  SEGREDOS GERADOS — SALVE EM LOCAL SEGURO (ex: Bitwarden)       ║\n'
  printf '  ╠══════════════════════════════════════════════════════════════════╣\n'
  printf "  ║  Domínio          : %-45s║\n" "$DOMAIN"
  printf "  ║  POSTGRES_PASSWORD: %-45s║\n" "$PG_PASS"
  printf "  ║  REDIS_PASSWORD   : %-45s║\n" "$REDIS_PASS"
  printf "  ║  FLOWER_USER      : %-45s║\n" "$FLOWER_USER"
  printf "  ║  FLOWER_PASSWORD  : %-45s║\n" "$FLOWER_PASS"
  printf "  ║  ASAAS_WH_TOKEN   : %-45s║\n" "$ASAAS_WH_TOKEN"
  printf "  ║  REVALIDATE_SECRET: %-45s║\n" "$REVALIDATE_SECRET"
  printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
  printf "${NC}\n"

  if [[ -z "${SMTP_PASS:-}" || -z "${ASAAS_KEY:-}" ]]; then
    warn "Campos deixados em branco:"
    [[ -z "${SMTP_PASS:-}" ]] && warn "  EMAIL_HOST_PASSWORD — edite depois: nano $ENV_FILE"
    [[ -z "${ASAAS_KEY:-}" ]] && warn "  ASAAS_API_KEY       — edite depois: nano $ENV_FILE"
  fi
fi

# ── Passo 5: Firewall ─────────────────────────────────────────────────────────
step "Firewall UFW"

if ufw status | grep -q "Status: active"; then
  warn "UFW já ativo — verifique com: ufw status"
else
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow ssh
  ufw --force enable
  success "UFW ativo — apenas SSH liberado (HTTP/HTTPS via Cloudflare Tunnel)"
fi

# ── Passo 6: Rede Docker ──────────────────────────────────────────────────────
step "Rede Docker para Cloudflare Tunnel"

if docker network ls | grep -q papermoon-network; then
  warn "Rede papermoon-network já existe"
else
  docker network create papermoon-network
  success "Rede papermoon-network criada"
fi

CLOUDFLARED_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i cloudflared | head -1 || true)
if [[ -n "$CLOUDFLARED_CONTAINER" ]]; then
  docker network connect papermoon-network "$CLOUDFLARED_CONTAINER" 2>/dev/null \
    && success "Container $CLOUDFLARED_CONTAINER conectado à papermoon-network" \
    || warn "$CLOUDFLARED_CONTAINER já estava na rede"
else
  warn "cloudflared não detectado. Após iniciar, execute:"
  warn "  docker network connect papermoon-network <nome-do-container>"
fi

# ── Passo 7: Primeiro deploy ──────────────────────────────────────────────────
step "Primeiro deploy"
cd "$APP_DIR"
sudo -u "$APP_USER" bash deploy.sh

# ── Passo 8: Backup automático ────────────────────────────────────────────────
step "Cron de backup automático (02:00 diário)"

mkdir -p "$APP_DIR/backups/daily" "$APP_DIR/backups/weekly" "$APP_DIR/backups/monthly"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/backups"
chmod +x "$APP_DIR/scripts/backup.sh"

touch /var/log/papermoon-backup.log
chown "$APP_USER:$APP_USER" /var/log/papermoon-backup.log
chmod 664 /var/log/papermoon-backup.log

CRON_MARKER="# papermoon-backup"
CRON_ENTRY="0 2 * * * $APP_DIR/scripts/backup.sh >> /var/log/papermoon-backup.log 2>&1 $CRON_MARKER"

if crontab -u "$APP_USER" -l 2>/dev/null | grep -q "$CRON_MARKER"; then
  warn "Cron de backup já instalado"
else
  (crontab -u "$APP_USER" -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -u "$APP_USER" -
  success "Cron instalado: backup diário às 02:00"
fi

# Logrotate
cat > /etc/logrotate.d/papermoon << LOGROTATE
$APP_DIR/deploys.log
/var/log/papermoon-backup.log {
    weekly
    rotate 12
    compress
    missingok
    notifempty
    create 640 $APP_USER $APP_USER
}
LOGROTATE
success "Logrotate configurado"

# ── Passo 9: Chave SSH para GitHub Actions ────────────────────────────────────
step "Chave SSH para deploy automático (GitHub Actions CD)"

SSH_DIR="/home/$APP_USER/.ssh"
DEPLOY_KEY="$SSH_DIR/papermoon_deploy_ed25519"

mkdir -p "$SSH_DIR"
chown "$APP_USER:$APP_USER" "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [[ ! -f "$DEPLOY_KEY" ]]; then
  sudo -u "$APP_USER" ssh-keygen -t ed25519 -C "papermoon-github-cd" -f "$DEPLOY_KEY" -N ""
  success "Par de chaves ED25519 gerado"
fi

AUTHORIZED_KEYS="$SSH_DIR/authorized_keys"
if ! grep -qF "$(cat "${DEPLOY_KEY}.pub")" "$AUTHORIZED_KEYS" 2>/dev/null; then
  cat "${DEPLOY_KEY}.pub" >> "$AUTHORIZED_KEYS"
  chown "$APP_USER:$APP_USER" "$AUTHORIZED_KEYS"
  chmod 600 "$AUTHORIZED_KEYS"
  success "Chave pública adicionada a authorized_keys"
fi

# ── Resumo final ───────────────────────────────────────────────────────────────
VPS_IP=$(curl -sf https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')

blank
printf "${BG}"
printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
printf '  ║                                                                  ║\n'
printf '  ║   PAPERMOON CONFIGURADO COM SUCESSO ✓                           ║\n'
printf '  ║                                                                  ║\n'
printf "  ║   diretório : %-51s║\n" "$APP_DIR"
printf "  ║   usuário   : %-51s║\n" "$APP_USER"
printf "  ║   VPS IP    : %-51s║\n" "${VPS_IP:-desconhecido}"
printf '  ║                                                                  ║\n'
printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
printf "${NC}\n"

printf "${BG}"
printf '  ┌──────────────────────────────────────────────────────────────────┐\n'
printf '  │  GitHub Actions CD — cole estes secrets em:                      │\n'
printf '  │  github.com/yurythx/papermoon → Settings → Secrets → Actions     │\n'
printf '  ├──────────────────────────────────────────────────────────────────┤\n'
printf "  │  PROD_SSH_HOST  →  %-47s│\n" "${VPS_IP:-<ip-da-vps>}"
printf "  │  PROD_SSH_PORT  →  %-47s│\n" "22"
printf "  │  PROD_SSH_USER  →  %-47s│\n" "$APP_USER"
printf "  │  PROD_APP_DIR   →  %-47s│\n" "$APP_DIR"
printf '  │  PROD_SSH_KEY   →  (chave privada abaixo)                        │\n'
printf '  └──────────────────────────────────────────────────────────────────┘\n'
printf "${NC}\n"

printf "${CY}"
printf '  ┌──────────────────────────────────────────────────────────────────┐\n'
printf '  │  PROD_SSH_KEY — copie tudo (inclusive BEGIN e END)               │\n'
printf '  ├──────────────────────────────────────────────────────────────────┤\n'
while IFS= read -r key_line; do
  printf "  │  %-66s│\n" "$key_line"
done < "$DEPLOY_KEY"
printf '  └──────────────────────────────────────────────────────────────────┘\n'
printf "${NC}\n"

printf "${BG}"
printf '  ┌──────────────────────────────────────────────────────────────────┐\n'
printf '  │  Próximos passos                                                  │\n'
printf '  ├──────────────────────────────────────────────────────────────────┤\n'
printf '  │  1. Cole os 5 secrets acima no GitHub                            │\n'
printf '  │  2. Crie o environment "production" em Settings → Environments   │\n'
printf '  │  3. Configure o Cloudflare Tunnel apontando para:                │\n'
printf '  │       app.<dominio>      → nextjs:3000                           │\n'
printf '  │       webhooks.<dominio> → django-api:8000                       │\n'
printf '  │  4. Crie o superusuário admin:                                   │\n'
printf '  │       make prod-superuser                                         │\n'
printf '  └──────────────────────────────────────────────────────────────────┘\n'
printf "${NC}\n"
