#!/bin/bash
# Service health monitoring for spondadmin
# Usage: ./monitoring/check-services.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
EXPECTED_CONTAINERS=4  # nginx, backend, frontend, db

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

check_service() {
    local name=$1
    local url=$2
    local expected=$3

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$HTTP_STATUS" = "$expected" ]; then
        echo -e "${GREEN}[OK]${NC} ${name} - HTTP ${HTTP_STATUS}"
    else
        echo -e "${RED}[FAIL]${NC} ${name} - HTTP ${HTTP_STATUS} (expected ${expected})"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "=== Spondadmin Service Check ==="
echo "Time: $(date)"
echo ""

# Check services
echo "--- HTTP Services ---"
check_service "Backend Health" "http://localhost:8001/health" "200"
check_service "Backend API" "http://localhost:8001/api/v1/docs" "200"
check_service "Frontend" "http://localhost:3000" "200"

# Check containers
echo ""
echo "--- Docker Containers ---"
cd "$PROJECT_DIR"
RUNNING=$(docker compose -f "$COMPOSE_FILE" ps --status running -q 2>/dev/null | wc -l)
if [ "$RUNNING" -eq "$EXPECTED_CONTAINERS" ]; then
    echo -e "${GREEN}[OK]${NC} ${RUNNING}/${EXPECTED_CONTAINERS} containers running"
else
    echo -e "${RED}[FAIL]${NC} ${RUNNING}/${EXPECTED_CONTAINERS} containers running"
    ERRORS=$((ERRORS + 1))
    docker compose -f "$COMPOSE_FILE" ps
fi

# Check database
echo ""
echo "--- Database ---"
DB_STATUS=$(docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "${POSTGRES_USER:-postgres}" 2>/dev/null && echo "ready" || echo "not ready")
if [ "$DB_STATUS" = "ready" ]; then
    echo -e "${GREEN}[OK]${NC} PostgreSQL is ready"
else
    echo -e "${RED}[FAIL]${NC} PostgreSQL is not ready"
    ERRORS=$((ERRORS + 1))
fi

# Disk usage
echo ""
echo "--- Disk Usage ---"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}[OK]${NC} Disk usage: ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}[WARN]${NC} Disk usage: ${DISK_USAGE}%"
else
    echo -e "${RED}[FAIL]${NC} Disk usage: ${DISK_USAGE}%"
    ERRORS=$((ERRORS + 1))
fi

# Memory usage
MEM_USAGE=$(free | awk '/Mem:/ {printf("%.0f", $3/$2 * 100)}')
if [ "$MEM_USAGE" -lt 80 ]; then
    echo -e "${GREEN}[OK]${NC} Memory usage: ${MEM_USAGE}%"
elif [ "$MEM_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}[WARN]${NC} Memory usage: ${MEM_USAGE}%"
else
    echo -e "${RED}[FAIL]${NC} Memory usage: ${MEM_USAGE}%"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All checks passed.${NC}"
    exit 0
else
    echo -e "${RED}${ERRORS} check(s) failed.${NC}"
    exit 1
fi
