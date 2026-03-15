#!/bin/bash
# Database backup script for spondadmin
# Usage: ./scripts/backup.sh
# Cron example: 0 2 * * * /path/to/spondadmin/scripts/backup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
LOG_DIR="/var/log/spondadmin"
LOG_FILE="${LOG_DIR}/backup.log"
RETENTION_DAYS=30

# Create directories
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting database backup..."

# Generate backup filename
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="${BACKUP_DIR}/spondadmin_scheduled_${TIMESTAMP}.dump"

# Run pg_dump via docker compose
cd "$PROJECT_DIR"
docker compose exec -T db pg_dump \
    -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-spond_admin}" \
    -Fc \
    > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed: ${BACKUP_FILE} (${SIZE})"
else
    log "ERROR: Backup failed!"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Compress with gzip if not already compressed by pg_dump custom format
# (pg_dump -Fc already compresses, so we skip this)

# Clean up old backups
DELETED=$(find "$BACKUP_DIR" -name "spondadmin_*.dump" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    log "Deleted ${DELETED} backup(s) older than ${RETENTION_DAYS} days"
fi

log "Backup process complete."
