#!/bin/bash
# Deployment script for spondadmin
# Usage: ./scripts/deploy.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"

cd "$PROJECT_DIR"

echo "=== Spondadmin Deployment ==="
echo "Started at: $(date)"
echo ""

# Step 1: Pre-deploy backup
echo "[1/9] Creating pre-deploy backup..."
if docker compose -f "$COMPOSE_FILE" ps db --status running -q 2>/dev/null | grep -q .; then
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    mkdir -p "${PROJECT_DIR}/backups"
    docker compose -f "$COMPOSE_FILE" exec -T db pg_dump \
        -U "${POSTGRES_USER:-postgres}" \
        -d "${POSTGRES_DB:-spond_admin}" \
        -Fc \
        > "${PROJECT_DIR}/backups/spondadmin_predeploy_${TIMESTAMP}.dump" \
        && echo "  Backup created." \
        || echo "  WARNING: Backup failed, continuing..."
else
    echo "  Database not running, skipping backup."
fi

# Step 2: Git pull
echo "[2/9] Pulling latest code..."
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
git pull --ff-only origin "$CURRENT_BRANCH"

# Step 3: Build images
echo "[3/9] Building Docker images..."
docker compose -f "$COMPOSE_FILE" build --no-cache

# Step 4: Stop containers
echo "[4/9] Stopping containers..."
docker compose -f "$COMPOSE_FILE" down

# Step 5: Start database
echo "[5/9] Starting database..."
docker compose -f "$COMPOSE_FILE" up -d db
echo "  Waiting for database to be ready..."
sleep 5

# Step 6: Run migrations
echo "[6/9] Running database migrations..."
docker compose -f "$COMPOSE_FILE" run --rm backend alembic upgrade head

# Step 6b: Bootstrap the first admin (idempotent — safe to re-run on every deploy).
# Read just the BOOTSTRAP_ADMIN_* keys from .env using grep. Bash-sourcing the
# .env file (`. .env`) is unsafe — values may contain spaces, quotes, or other
# shell metacharacters (e.g. `PROJECT_NAME=Spond Admin API` would make bash
# try to run "Admin" as a command). Docker compose reads .env natively without
# this hazard; this loop here only needs three specific keys.
_env_get() {
    # _env_get FILE KEY → prints the unquoted value (or empty if absent).
    [ -f "$1" ] || return 0
    grep -E "^$2=" "$1" | tail -1 | cut -d= -f2- | sed -E 's/^"(.*)"$/\1/;s/^'\''(.*)'\''$/\1/'
}
ENV_FILE="${PROJECT_DIR}/.env"
BOOTSTRAP_ADMIN_EMAIL="$(_env_get "$ENV_FILE" BOOTSTRAP_ADMIN_EMAIL)"
BOOTSTRAP_ADMIN_ROLE="$(_env_get "$ENV_FILE" BOOTSTRAP_ADMIN_ROLE)"
BOOTSTRAP_ADMIN_FULL_NAME="$(_env_get "$ENV_FILE" BOOTSTRAP_ADMIN_FULL_NAME)"
if [ -n "${BOOTSTRAP_ADMIN_EMAIL}" ]; then
    echo "[6b] Seeding bootstrap admin (${BOOTSTRAP_ADMIN_EMAIL})..."
    docker compose -f "$COMPOSE_FILE" run --rm backend python3 seed_first_admin.py \
        --email "${BOOTSTRAP_ADMIN_EMAIL}" \
        --role "${BOOTSTRAP_ADMIN_ROLE:-admin}" \
        ${BOOTSTRAP_ADMIN_FULL_NAME:+--full-name "${BOOTSTRAP_ADMIN_FULL_NAME}"} \
        || echo "  WARNING: bootstrap admin seeding failed (see output above); continuing."
else
    echo "[6b] BOOTSTRAP_ADMIN_EMAIL not set in $ENV_FILE — skipping admin seed step."
fi

# Step 7: Start all services
echo "[7/9] Starting all services..."
docker compose -f "$COMPOSE_FILE" up -d

# Step 8: Health check
echo "[8/9] Running health checks..."
MAX_ATTEMPTS=30
ATTEMPT=0
HEALTHY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health 2>/dev/null || echo "000")

    if [ "$HTTP_STATUS" = "200" ]; then
        HEALTHY=true
        echo "  Backend healthy after ${ATTEMPT} attempt(s)."
        break
    fi

    echo "  Attempt ${ATTEMPT}/${MAX_ATTEMPTS} - status: ${HTTP_STATUS}"
    sleep 5
done

if [ "$HEALTHY" = false ]; then
    echo "  WARNING: Health check failed after ${MAX_ATTEMPTS} attempts!"
    echo "  Check logs: docker compose -f $COMPOSE_FILE logs backend"
fi

# Step 9: Cleanup
echo "[9/9] Cleaning up old Docker images..."
docker image prune -f

echo ""
echo "=== Deployment Complete ==="
echo "Finished at: $(date)"
docker compose -f "$COMPOSE_FILE" ps
