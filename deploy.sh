#!/usr/bin/env bash
#
# deploy.sh — Deploy de nova versão em produção
#
# Uso:
#   bash deploy.sh              # deploy padrão (pull + build + restart)
#   bash deploy.sh --skip-pull  # não faz git pull (útil para rebuild forçado)
#   bash deploy.sh --no-cache   # rebuild completo sem cache Docker
#
set -euo pipefail

# ── Opções ────────────────────────────────────────────────────────────────────
SKIP_PULL=false
NO_CACHE=false
for arg in "$@"; do
  case $arg in
    --skip-pull) SKIP_PULL=true ;;
    --no-cache)  NO_CACHE=true  ;;
  esac
done

# ── Paleta Matrix (apenas verdes + vermelho para erros) ───────────────────────
G='\033[0;32m'    # verde
BG='\033[1;32m'   # verde brilhante
DG='\033[2;32m'   # verde escuro / chuva
RE='\033[0;31m'   # vermelho — só para erros
NC='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────
_ts()     { date '+%H:%M:%S'; }
info()    { printf "${G}  ◈  ${NC}%s\n"        "$*"; }
success() { printf "${BG}  ✓  ${NC}%s\n"        "$*"; }
warn()    { printf "${G}  ⚡ ${NC}%s\n"          "$*"; }
error()   { printf "${RE}  ✗  ${NC}%s\n" "$*" >&2; }
die()     { error "$*"; log "FALHOU: $*"; exit 1; }

_STEP=0
step() {
  _STEP=$(( _STEP + 1 ))
  printf "\n${BG}"
  printf '  ┌──────────────────────────────────────────────────────────────┐\n'
  printf "  │  [%02d]  %-56s│\n" "$_STEP" "$*"
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
  local DT="$1" COMMIT="$2"
  printf "${BG}"
  printf '\n'
  printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
  printf '  ║                                                                  ║\n'
  printf '  ║   ██████╗ ██╗██╗███████╗███████╗███╗  ██╗                      ║\n'
  printf '  ║   ██╔══██╗██║██║██╔════╝██╔════╝████╗ ██║   ┌─────────────┐   ║\n'
  printf '  ║   ██████╔╝██║██║███████╗███████╗██╔██╗██║   │   DEPLOY    │   ║\n'
  printf '  ║   ██╔══██╗██║██║╚════██║╚════██║██║╚████║   └─────────────┘   ║\n'
  printf '  ║   ██║  ██║██║██║███████║███████║██║ ╚███║                      ║\n'
  printf '  ║   ╚═╝  ╚═╝╚═╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝                      ║\n'
  printf "  ║   %-64s║\n" "$DT   commit: $COMMIT"
  printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
  printf '\n'
  printf "${NC}"
}

# ── Configuração ──────────────────────────────────────────────────────────────
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE="docker compose -f $APP_DIR/docker-compose.prod.yml --env-file $APP_DIR/.env.production"
LOG_FILE="$APP_DIR/deploys.log"
HEALTH_URL="http://localhost:8000/health/"
HEALTH_RETRIES=15
HEALTH_SLEEP=8
GIT_BRANCH="${GIT_BRANCH:-main}"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE"; }

cd "$APP_DIR"

# ── Intro ─────────────────────────────────────────────────────────────────────
_rain

PREV_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
_banner "$(date '+%Y-%m-%d %H:%M:%S')" "$PREV_COMMIT"

# ── Pré-verificações ──────────────────────────────────────────────────────────
step "Verificando pré-requisitos"

[[ -f ".env.production" ]] \
  || die ".env.production não encontrado. Copie .env.production.example e preencha."

command -v docker >/dev/null 2>&1 \
  || die "Docker não instalado."

docker info >/dev/null 2>&1 \
  || die "Docker daemon não está rodando. Execute: sudo systemctl start docker"

command -v curl >/dev/null 2>&1 \
  || die "curl não encontrado. Instale: apt-get install -y curl"

docker network ls | grep -q papermoon-network \
  || { warn "Rede papermoon-network não existe. Criando..."; docker network create papermoon-network; }

success "Pré-requisitos OK"

# ── Git pull ──────────────────────────────────────────────────────────────────
step "Atualizando código"

if [[ "$SKIP_PULL" == "true" ]]; then
  warn "--skip-pull: pulando git pull"
  NEW_COMMIT="$PREV_COMMIT"
else
  git fetch origin --quiet
  git pull origin "$GIT_BRANCH" --ff-only --quiet \
    || die "git pull falhou. Verifique conflitos ou use --skip-pull."
  NEW_COMMIT=$(git rev-parse --short HEAD)
fi

if [[ "$PREV_COMMIT" == "$NEW_COMMIT" ]]; then
  warn "Nenhuma alteração de código (commit: $NEW_COMMIT). Prosseguindo com rebuild."
else
  success "Código: $PREV_COMMIT → $NEW_COMMIT"
fi

DEPLOY_START=$(date '+%Y-%m-%d %H:%M:%S')
log "Deploy iniciado | commit: $NEW_COMMIT (anterior: $PREV_COMMIT) | branch: $GIT_BRANCH"

# ── Rollback ──────────────────────────────────────────────────────────────────
_rollback() {
  local exit_code=$?
  if [[ $exit_code -ne 0 ]]; then
    printf '\n'
    error "Deploy FALHOU (código $exit_code). Iniciando rollback..."
    log "ROLLBACK iniciado"
    git checkout "$PREV_COMMIT" -- . 2>/dev/null || true
    $COMPOSE up -d 2>/dev/null || true
    log "ROLLBACK concluído — commit restaurado para $PREV_COMMIT"
    printf '\n'
    error "Rollback concluído. Verifique:"
    error "  $COMPOSE logs --tail=80"
    printf '\n'
    printf "${RE}"
    printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
    printf '  ║   SISTEMA RESTAURADO PARA O COMMIT ANTERIOR                      ║\n'
    printf "  ║   %-64s║\n" "commit: $PREV_COMMIT"
    printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
    printf "${NC}\n"
  fi
}
trap _rollback EXIT

# ── Build de imagens ──────────────────────────────────────────────────────────
step "Construindo imagens Docker"
BUILD_FLAGS="--parallel"
[[ "$NO_CACHE" == "true" ]] && BUILD_FLAGS="$BUILD_FLAGS --no-cache"
$COMPOSE build $BUILD_FLAGS
success "Imagens construídas"

# ── Chaves JWT RS256 ──────────────────────────────────────────────────────────
step "Verificando chaves JWT RS256"
if grep -qE '^JWT_PRIVATE_KEY=.+' .env.production && grep -qE '^JWT_PUBLIC_KEY=.+' .env.production; then
  success "Chaves JWT já configuradas em .env.production"
else
  warn "Chaves JWT ausentes — gerando par RSA-2048 automaticamente"

  JWT_OUTPUT=$($COMPOSE run --rm --no-deps \
    -e DJANGO_SETTINGS_MODULE=core.settings.local \
    django-api python manage.py generate_jwt_keys)

  JWT_PRIVATE_LINE=$(echo "$JWT_OUTPUT" | grep '^JWT_PRIVATE_KEY=')
  JWT_PUBLIC_LINE=$(echo "$JWT_OUTPUT" | grep '^JWT_PUBLIC_KEY=')

  [[ -n "$JWT_PRIVATE_LINE" && -n "$JWT_PUBLIC_LINE" ]] \
    || die "Falha ao gerar chaves JWT."

  python3 - "$JWT_PRIVATE_LINE" "$JWT_PUBLIC_LINE" <<'PYEOF'
import sys
private_line, public_line = sys.argv[1], sys.argv[2]
path = ".env.production"
with open(path, encoding="utf-8") as f:
    lines = f.readlines()
with open(path, "w", encoding="utf-8") as f:
    for line in lines:
        if line.startswith("JWT_PRIVATE_KEY="):
            f.write(private_line + "\n")
        elif line.startswith("JWT_PUBLIC_KEY="):
            f.write(public_line + "\n")
        else:
            f.write(line)
PYEOF

  success "Chaves JWT geradas e salvas em .env.production"
fi

# ── Banco de dados e cache ────────────────────────────────────────────────────
step "Iniciando banco de dados e cache"
$COMPOSE up -d postgres redis
_PG_USER=$(grep -E '^POSTGRES_USER=' .env.production | cut -d= -f2 | tr -d ' \r')
_PG_DB=$(grep   -E '^POSTGRES_DB='   .env.production | cut -d= -f2 | tr -d ' \r')
_PG_USER="${_PG_USER:-papermoon}"
_PG_DB="${_PG_DB:-papermoon}"
_db_ready=false
for i in $(seq 1 40); do
  if $COMPOSE exec -T postgres psql -U "$_PG_USER" -d "$_PG_DB" -c "SELECT 1" >/dev/null 2>&1; then
    _db_ready=true; break
  fi
  sleep 3
done
[[ "$_db_ready" == "true" ]] || die "Postgres não ficou pronto após 120s."
success "Banco de dados e cache prontos"

# ── Migrations ────────────────────────────────────────────────────────────────
step "Aplicando migrations"
$COMPOSE run --rm --no-deps \
  -e DJANGO_SETTINGS_MODULE=core.settings.production \
  django-api python manage.py migrate --noinput
success "Migrations aplicadas"

# ── Static files ──────────────────────────────────────────────────────────────
step "Coletando static files"
$COMPOSE run --rm --no-deps \
  -e DJANGO_SETTINGS_MODULE=core.settings.production \
  django-api python manage.py collectstatic --noinput --clear
success "Static files coletados"

# ── Django checks ─────────────────────────────────────────────────────────────
step "Django system check"
$COMPOSE run --rm --no-deps \
  -e DJANGO_SETTINGS_MODULE=core.settings.production \
  django-api python manage.py check --deploy 2>&1 \
  | grep -E "^(System check|ERROR|WARNING)" || true
success "System check OK"

# ── Restart dos serviços ──────────────────────────────────────────────────────
step "Reiniciando serviços"
$COMPOSE up -d --remove-orphans
success "Serviços reiniciados"

# ── Health check ──────────────────────────────────────────────────────────────
step "Verificação de saúde do sistema"
HEALTHY=false

_progress_bar() {
  local current="$1" total="$2"
  local filled=$(( current * 40 / total ))
  local empty=$(( 40 - filled ))
  printf "${G}  ["
  printf '%0.s▓' $(seq 1 $filled)
  printf '%0.s░' $(seq 1 $empty)
  printf "] %02d/%02d${NC}\r" "$current" "$total"
}

for i in $(seq 1 $HEALTH_RETRIES); do
  _progress_bar "$i" "$HEALTH_RETRIES"
  # Run curl inside the django-api container (port 8000 is not exposed to the host in prod).
  # Use -H 'Host: django-api' because localhost is not in ALLOWED_HOSTS.
  if RESPONSE=$($COMPOSE exec -T django-api curl -sf --max-time 5 -H 'Host: django-api' http://localhost:8000/health/ 2>/dev/null); then
    if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('data',{}).get('db')=='ok' and d.get('data',{}).get('redis')=='ok' else 1)" 2>/dev/null; then
      HEALTHY=true
      printf '\n'
      success "Sistema saudável (tentativa $i/$HEALTH_RETRIES)"
      printf "${G}"
      echo "$RESPONSE" | python3 -c \
        'import sys,json; d=json.load(sys.stdin); [print(f"     {k:12s} {v}") for k,v in d.items()]' \
        2>/dev/null || true
      printf "${NC}"
      break
    else
      warn "Degradado ($i/$HEALTH_RETRIES): $RESPONSE"
    fi
  fi
  sleep $HEALTH_SLEEP
done

[[ "$HEALTHY" == "true" ]] \
  || die "Health check falhou após $((HEALTH_RETRIES * HEALTH_SLEEP))s. Verifique os logs."

# ── Status dos containers ─────────────────────────────────────────────────────
step "Status dos containers"
printf "${G}"
$COMPOSE ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
printf "${NC}"

# ── Limpeza ───────────────────────────────────────────────────────────────────
step "Limpando imagens antigas"
docker image prune -f --filter "until=72h" > /dev/null 2>&1 || true
success "Imagens antigas removidas"

# ── Sucesso ───────────────────────────────────────────────────────────────────
trap - EXIT

DURATION=$(( $(date +%s) - $(date -d "$DEPLOY_START" +%s 2>/dev/null || echo "$(date +%s)") ))
log "Deploy CONCLUÍDO | commit: $NEW_COMMIT | duração: ${DURATION}s"

printf "${BG}"
printf '\n'
printf '  ╔══════════════════════════════════════════════════════════════════╗\n'
printf '  ║                                                                  ║\n'
printf '  ║   DEPLOY CONCLUÍDO COM SUCESSO                                   ║\n'
printf '  ║                                                                  ║\n'
printf "  ║   commit  :  %-51s║\n" "$PREV_COMMIT → $NEW_COMMIT"
printf "  ║   iniciado:  %-51s║\n" "$DEPLOY_START"
printf "  ║   duração :  %-51s║\n" "${DURATION}s"
printf '  ║                                                                  ║\n'
printf '  ╚══════════════════════════════════════════════════════════════════╝\n'
printf '\n'
printf "${G}"
printf "  ◈  logs    →  %s logs -f\n" "$COMPOSE"
printf "  ◈  status  →  %s ps\n"      "$COMPOSE"
printf "  ◈  health  →  curl %s\n"    "$HEALTH_URL"
printf "  ◈  deploys →  tail -f %s\n" "$LOG_FILE"
printf '\n'
printf "${NC}"
