#!/usr/bin/env bash
#
# setup.sh — Configuração inicial da VPS para o PaperMoon
#
# O que este script faz (9 passos):
#   1. Atualiza o sistema e instala dependências base
#   2. Instala Docker + Docker Compose
#   3. Cria o usuário de aplicação "papermoon"
#   4. Cria .env.production a partir do exemplo e pede preenchimento
#   5. Configura o firewall UFW (apenas SSH — HTTP/S via Cloudflare Tunnel)
#   6. Cria a rede Docker "papermoon-network" e conecta o cloudflared
#   7. Executa o primeiro deploy (build + migrate + health check)
#   8. Instala cron de backup diário às 02:00 com rotação automática
#   9. Gera chave SSH ED25519 para deploy automático via GitHub Actions
#      e imprime os secrets que devem ser cadastrados no GitHub
#
# Pré-requisitos:
#   - Ubuntu 22.04+ ou Debian 12+
#   - Executar a partir do diretório clonado do repositório
#   - Cloudflare Tunnel já instalado na VPS (cloudflared rodando)
#
# Uso:
#   sudo bash setup.sh
#
set -euo pipefail

# ── Paleta Matrix (apenas verdes + vermelho para erros) ───────────────────────
G='\033[0;32m'
BG='\033[1;32m'
DG='\033[2;32m'
RE='\033[0;31m'
NC='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { printf "${G}  ◈  ${NC}%s\n"        "$*"; }
success() { printf "${BG}  ✓  ${NC}%s\n"        "$*"; }
warn()    { printf "${G}  ⚡ ${NC}%s\n"          "$*"; }
error()   { printf "${RE}  ✗  ${NC}%s\n" "$*" >&2; }
die()     { error "$*"; exit 1; }

_STEP=0
step() {
  _STEP=$(( _STEP + 1 ))
  printf "\n${BG}"
  printf '  ┌──────────────────────────────────────────────────────────────┐\n'
  printf "  │  [%02d/09]  %-53s│\n" "$_STEP" "$*"
  printf '  └──────────────────────────────────────────────────────────────┘\n'
  printf "${NC}"
}

# ── Chuva Matrix (intro) ──────────────────────────────────────────────────────
_rain() {
  local COLS CHARS i j idx line
  COLS=${COLUMNS:-$(tput cols 2>/dev/null || echo 80)}
  CHARS='ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789'
  printf "${DG}"
  for ((i=0; i<5; i++)); do
    line=""
    for ((j=0; j<COLS; j++)); do
      idx=$(( RANDOM % ${#CHARS} ))
      line+="${CHARS:$idx:1}"
    done
    printf '%s\n' "$line"
    sleep 0.05
  done
  printf "${NC}"
}

# ── Banner ────────────────────────────────────────────────────────────────────
_banner() {
  local OS_INFO="$1"
  printf "${BG}"
  printf '\n'
  printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
  printf '  ║                                                                  ║\n'
  printf '  ║   ██████╗ ██╗██╗███████╗███████╗███╗  ██╗                      ║\n'
  printf '  ║   ██╔══██╗██║██║██╔════╝██╔════╝████╗ ██║   ┌─────────────┐   ║\n'
  printf '  ║   ██████╔╝██║██║███████╗███████╗██╔██╗██║   │    SETUP    │   ║\n'
  printf '  ║   ██╔══██╗██║██║╚════██║╚════██║██║╚████║   └─────────────┘   ║\n'
  printf '  ║   ██║  ██║██║██║███████║███████║██║ ╚███║                      ║\n'
  printf '  ║   ╚═╝  ╚═╝╚═╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝                      ║\n'
  printf "  ║   %-64s║\n" "$OS_INFO"
  printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
  printf '\n'
  printf "${NC}"
}

# ── Verificação de root ───────────────────────────────────────────────────────
[[ $EUID -ne 0 ]] && die "Execute com sudo: sudo bash setup.sh"

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_rain
_banner "$(lsb_release -ds 2>/dev/null || uname -s)   dir: $APP_DIR"

# ── Passo 1: Sistema ─────────────────────────────────────────────────────────
step "Atualizando sistema e instalando dependências"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq
apt-get install -y -qq \
  ca-certificates gnupg lsb-release curl git unzip jq htop logrotate ufw
success "Sistema atualizado"

# ── Passo 2: Docker ──────────────────────────────────────────────────────────
step "Docker + Docker Compose"
if command -v docker >/dev/null 2>&1; then
  warn "Docker já instalado: $(docker --version)"
else
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
  success "Docker instalado: $(docker --version)"
fi

# ── Passo 3: Usuário da aplicação ────────────────────────────────────────────
step "Usuário de aplicação"
APP_USER="${APP_USER:-papermoon}"
if id "$APP_USER" &>/dev/null; then
  warn "Usuário $APP_USER já existe"
else
  useradd -r -m -s /bin/bash -d "/home/$APP_USER" "$APP_USER"
  success "Usuário $APP_USER criado"
fi
usermod -aG docker "$APP_USER"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
success "Permissões ajustadas ($APP_USER pode usar Docker)"

# ── Passo 4: Variáveis de ambiente ───────────────────────────────────────────
step "Configuração do ambiente de produção"
ENV_FILE="$APP_DIR/.env.production"

if [[ -f "$ENV_FILE" ]]; then
  warn ".env.production já existe — mantendo. Edite manualmente se necessário."
else
  [[ -f "$APP_DIR/.env.production.example" ]] \
    || die ".env.production.example não encontrado em $APP_DIR"

  cp "$APP_DIR/.env.production.example" "$ENV_FILE"
  chown "$APP_USER:$APP_USER" "$ENV_FILE"
  chmod 600 "$ENV_FILE"

  printf "\n${BG}"
  printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
  printf '  ║   AÇÃO NECESSÁRIA                                                ║\n'
  printf '  ║                                                                  ║\n'
  printf "  ║   Preencha todos os CHANGE-ME no arquivo:                        ║\n"
  printf "  ║   %-64s║\n" "nano $ENV_FILE"
  printf '  ║                                                                  ║\n'
  printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
  printf "${NC}\n"

  read -rp "  Pressione Enter após preencher o .env.production..."
  [[ -s "$ENV_FILE" ]] || die ".env.production está vazio."
fi
success ".env.production configurado"

# ── Passo 5: Firewall ────────────────────────────────────────────────────────
step "Firewall UFW"
if ! ufw status | grep -q "Status: active"; then
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow ssh
  ufw --force enable
  success "UFW ativo — apenas SSH liberado (HTTP/HTTPS via Cloudflare Tunnel)"
else
  warn "UFW já ativo — verifique: ufw status"
fi

# ── Passo 6: Rede Docker para Cloudflare Tunnel ──────────────────────────────
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
    || warn "Container $CLOUDFLARED_CONTAINER já conectado à papermoon-network"
else
  warn "cloudflared não detectado. Após iniciar, execute:"
  warn "  docker network connect papermoon-network <container>"
fi

# ── Passo 7: Primeiro deploy ─────────────────────────────────────────────────
step "Primeiro deploy"
cd "$APP_DIR"
sudo -u "$APP_USER" bash deploy.sh

# ── Passo 8: Backup automático ───────────────────────────────────────────────
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

# ── Passo 9: Chave SSH para GitHub Actions ───────────────────────────────────
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

# ── Logrotate ─────────────────────────────────────────────────────────────────
cat > /etc/logrotate.d/papermoon <<EOF
$APP_DIR/deploys.log
/var/log/papermoon-backup.log {
    weekly
    rotate 12
    compress
    missingok
    notifempty
    create 640 $APP_USER $APP_USER
}
EOF
success "Logrotate configurado"

# ── Resumo final ─────────────────────────────────────────────────────────────
VPS_IP=$(curl -sf https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')

printf '\n'
printf "${BG}"
printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
printf '  ║                                                                  ║\n'
printf '  ║   PAPERMOON CONFIGURADO COM SUCESSO                              ║\n'
printf '  ║                                                                  ║\n'
printf "  ║   dir     :  %-51s║\n" "$APP_DIR"
printf "  ║   usuário :  %-51s║\n" "$APP_USER"
printf "  ║   VPS IP  :  %-51s║\n" "${VPS_IP:-desconhecido}"
printf '  ║                                                                  ║\n'
printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
printf "${NC}\n"

printf "${BG}"
printf '  ┌──────────────────────────────────────────────────────────────────┐\n'
printf '  │  GitHub Actions CD — cole estes secrets em:                      │\n'
printf '  │  github.com → Settings → Secrets → Actions → New secret          │\n'
printf '  ├──────────────────────────────────────────────────────────────────┤\n'
printf "  │  PROD_SSH_HOST  →  %-47s│\n" "${VPS_IP:-<ip-da-vps>}"
printf "  │  PROD_SSH_PORT  →  %-47s│\n" "22"
printf "  │  PROD_SSH_USER  →  %-47s│\n" "$APP_USER"
printf "  │  PROD_APP_DIR   →  %-47s│\n" "$APP_DIR"
printf '  │  PROD_SSH_KEY   →  (chave abaixo)                                │\n'
printf '  └──────────────────────────────────────────────────────────────────┘\n'
printf "${NC}\n"

printf "${DG}"
printf '  ┌──────────────────────────────────────────────────────────────────┐\n'
printf '  │  PROD_SSH_KEY (copie tudo, inclusive BEGIN e END)                │\n'
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
printf "  │  2. Crie o environment 'production' em Settings → Environments   │\n"
printf '  │  3. Configure o Cloudflare Tunnel:                               │\n'
printf '  │       cat cloudflared/config.yml.example                         │\n'
printf '  │  4. Aponte app.papermoon.example.com e webhooks.papermoon.example.com │\n'
printf '  │  5. Crie o superusuário admin:                                   │\n'
printf '  │       make prod-superuser                                         │\n'
printf '  └──────────────────────────────────────────────────────────────────┘\n'
printf "${NC}\n"
