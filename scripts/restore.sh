#!/bin/bash
# Database restore script for spondadmin
# Usage: ./scripts/restore.sh <backup_file>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -la "${PROJECT_DIR}/backups/"*.dump 2>/dev/null || echo "  No backups found."
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "WARNING: This will restore the database from: ${BACKUP_FILE}"
echo "All current data will be replaced."
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Create safety backup first
echo "Creating safety backup before restore..."
SAFETY_TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
SAFETY_FILE="${PROJECT_DIR}/backups/spondadmin_pre_restore_${SAFETY_TIMESTAMP}.dump"

cd "$PROJECT_DIR"
docker compose exec -T db pg_dump \
    -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-spond_admin}" \
    -Fc \
    > "$SAFETY_FILE"

echo "Safety backup created: ${SAFETY_FILE}"

# Restore
echo "Restoring database..."
docker compose exec -T db pg_restore \
    -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-spond_admin}" \
    --clean \
    --if-exists \
    < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Database restored successfully from: ${BACKUP_FILE}"
else
    echo "WARNING: pg_restore reported warnings (this is often normal for --clean restores)"
    echo "Verify your data is correct."
fi
