#!/usr/bin/env bash
#
# scripts/backup.sh — PaperMoon PostgreSQL backup
#
# Features:
#   - Daily, weekly (Sunday) and monthly (1st) snapshots
#   - Local rotation: 7 daily / 4 weekly / 3 monthly
#   - Optional cloud sync via rclone (any provider: B2, S3, GCS…)
#   - Exit code 1 on pg_dump failure so cron mails the error
#
# Usage:
#   bash scripts/backup.sh              # normal run
#   bash scripts/backup.sh --no-rotate  # skip deletion of old backups
#
# Install cron (2 AM daily):
#   bash scripts/setup-cron.sh
#
# Restore:
#   export $(grep -E '^(POSTGRES_DB|POSTGRES_USER)=' .env.production | xargs)
#   gunzip -c backups/daily/papermoon_TIMESTAMP.sql.gz | \
#   docker compose -f docker-compose.prod.yml --env-file .env.production \
#     exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
#
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="docker compose -f $APP_DIR/docker-compose.prod.yml --env-file $APP_DIR/.env.production"

BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DAY_OF_WEEK=$(date +%u)     # 1=Mon … 7=Sun
DAY_OF_MONTH=$(date +%d)    # 01–31
NO_ROTATE=false

for arg in "$@"; do
  [[ "$arg" == "--no-rotate" ]] && NO_ROTATE=true
done

# Retention periods (in days)
DAILY_RETENTION="${DAILY_RETENTION:-7}"
WEEKLY_RETENTION="${WEEKLY_RETENTION:-28}"   # 4 weeks
MONTHLY_RETENTION="${MONTHLY_RETENTION:-90}" # 3 months

# Load .env.production so POSTGRES_* vars are available
# shellcheck disable=SC1091
[[ -f "$APP_DIR/.env.production" ]] && set -a && source "$APP_DIR/.env.production" && set +a

POSTGRES_DB="${POSTGRES_DB:-papermoon}"
POSTGRES_USER="${POSTGRES_USER:-papermoon}"

# ── Helpers ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
_ts()     { date '+%Y-%m-%d %H:%M:%S'; }
info()    { echo -e "[$(_ts)] ${BLUE}INFO${NC}  $*"; }
success() { echo -e "[$(_ts)] ${GREEN}OK${NC}    $*"; }
warn()    { echo -e "[$(_ts)] ${YELLOW}WARN${NC}  $*"; }
error()   { echo -e "[$(_ts)] ${RED}ERROR${NC} $*" >&2; }

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ -f "$APP_DIR/.env.production" ]] \
  || { error ".env.production not found at $APP_DIR — aborting"; exit 1; }

$COMPOSE exec -T postgres pg_isready -U "$POSTGRES_USER" -q \
  || { error "Postgres is not ready — aborting backup"; exit 1; }

mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly" "$BACKUP_DIR/monthly"

info "Starting backup — db=$POSTGRES_DB user=$POSTGRES_USER"

# ── Dump function ─────────────────────────────────────────────────────────────
_dump() {
  local dest="$1" label="$2"
  local file="$dest/papermoon_${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

  info "$label → $file"

  if $COMPOSE exec -T postgres \
      pg_dump -U "$POSTGRES_USER" --no-owner --no-acl "$POSTGRES_DB" \
    | gzip -9 > "$file"; then
    local size; size=$(du -sh "$file" | cut -f1)
    success "$label backup complete ($size)"
  else
    error "$label pg_dump failed"
    rm -f "$file"
    return 1
  fi
}

# ── Backups ───────────────────────────────────────────────────────────────────
_dump "$BACKUP_DIR/daily" "Daily"

[[ "$DAY_OF_WEEK" == "7" ]] && _dump "$BACKUP_DIR/weekly" "Weekly"

[[ "$DAY_OF_MONTH" == "01" ]] && _dump "$BACKUP_DIR/monthly" "Monthly"

# ── Rotation ──────────────────────────────────────────────────────────────────
if [[ "$NO_ROTATE" == "false" ]]; then
  info "Rotating old backups..."
  find "$BACKUP_DIR/daily"   -name "*.sql.gz" -mtime +"$DAILY_RETENTION"   -delete
  find "$BACKUP_DIR/weekly"  -name "*.sql.gz" -mtime +"$WEEKLY_RETENTION"  -delete
  find "$BACKUP_DIR/monthly" -name "*.sql.gz" -mtime +"$MONTHLY_RETENTION" -delete
  success "Rotation done (daily=$DAILY_RETENTION d, weekly=$((WEEKLY_RETENTION/7)) wk, monthly=$((MONTHLY_RETENTION/30)) mo)"
fi

# ── Cloud sync (optional) ─────────────────────────────────────────────────────
# Set BACKUP_RCLONE_REMOTE in .env.production, e.g.:
#   BACKUP_RCLONE_REMOTE=b2:my-bucket/papermoon-backups
#   BACKUP_RCLONE_REMOTE=s3:my-bucket/papermoon-backups
if [[ -n "${BACKUP_RCLONE_REMOTE:-}" ]]; then
  if command -v rclone &>/dev/null; then
    info "Cloud sync → ${BACKUP_RCLONE_REMOTE}"
    rclone sync "$BACKUP_DIR" "${BACKUP_RCLONE_REMOTE}" \
      --log-level WARNING \
      --stats-one-line \
      --transfers 4
    success "Cloud sync complete"
  else
    warn "BACKUP_RCLONE_REMOTE is set but rclone is not installed — skipping cloud sync"
    warn "Install rclone: curl https://rclone.org/install.sh | sudo bash"
  fi
fi

success "Backup finished"
