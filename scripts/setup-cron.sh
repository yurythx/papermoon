#!/usr/bin/env bash
#
# scripts/setup-cron.sh — Installs the PaperMoon daily backup cron job
#
# Run once on the VPS after cloning the repo:
#   bash scripts/setup-cron.sh
#
# What it does:
#   1. Installs a cron entry: runs backup.sh at 02:00 every day
#   2. Creates the log file at /var/log/papermoon-backup.log
#   3. Prints the crontab to confirm
#
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_SCRIPT="$APP_DIR/scripts/backup.sh"
LOG_FILE="/var/log/papermoon-backup.log"
CRON_MARKER="# papermoon-backup"
CRON_ENTRY="0 2 * * * $BACKUP_SCRIPT >> $LOG_FILE 2>&1 $CRON_MARKER"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
success() { echo -e "  ${GREEN}✓${NC} $*"; }
warn()    { echo -e "  ${YELLOW}!${NC} $*"; }
error()   { echo -e "  ${RED}✗${NC} $*" >&2; exit 1; }

echo ""
echo "PaperMoon — Setup backup cron job"
echo "────────────────────────────────"

# Make backup.sh executable
chmod +x "$BACKUP_SCRIPT"
success "backup.sh is executable"

# Create log file
sudo touch "$LOG_FILE"
sudo chmod 664 "$LOG_FILE"
sudo chown "$USER":"$USER" "$LOG_FILE" 2>/dev/null || true
success "Log file: $LOG_FILE"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "$CRON_MARKER"; then
  warn "Cron job already installed:"
  crontab -l | grep "$CRON_MARKER"
  echo ""
  echo "To reinstall, remove the existing entry and run this script again."
  exit 0
fi

# Install cron entry
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
success "Cron job installed (runs at 02:00 daily)"

echo ""
echo "Current crontab:"
crontab -l
echo ""
echo -e "${GREEN}Done!${NC} Backup logs: tail -f $LOG_FILE"
echo "Manual backup: make prod-backup"
echo ""
