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
git pull --ff-only

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
