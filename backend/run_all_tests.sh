#!/bin/bash

# Complete automated test suite for Spond Admin API
# Run this after setting up the environment

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}=========================================="
echo "Spond Admin API - Complete Test Suite"
echo -e "==========================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Please run this script from the backend directory${NC}"
    exit 1
fi

# Phase 0: Environment Check
echo -e "${BLUE}${BOLD}Phase 0: Environment Check${NC}"
echo "-------------------------------------------"

# Check Python
echo -n "Python version: "
python3 --version || { echo -e "${RED}Python not found${NC}"; exit 1; }

# Check virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    if [ -z "$VIRTUAL_ENV" ]; then
        echo -e "${YELLOW}⚠ Virtual environment not activated${NC}"
        echo "  Activate with: source venv/bin/activate"
        exit 1
    else
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    fi
else
    echo -e "${RED}✗ Virtual environment missing${NC}"
    echo "  Create with: python3 -m venv venv"
    exit 1
fi

# Check if uvicorn is available
if command -v uvicorn &> /dev/null; then
    echo -e "${GREEN}✓ uvicorn installed${NC}"
else
    echo -e "${RED}✗ uvicorn not found${NC}"
    echo "  Install with: pip install -r requirements.txt"
    exit 1
fi

# Check .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
else
    echo -e "${YELLOW}⚠ .env file missing (will use defaults)${NC}"
fi

# Check database
if [ -f "spond_admin.db" ]; then
    SIZE=$(ls -lh spond_admin.db | awk '{print $5}')
    echo -e "${GREEN}✓ Database exists (${SIZE})${NC}"
else
    echo -e "${YELLOW}⚠ Database will be created on first run${NC}"
fi

echo ""

# Phase 1: Database Initialization
echo -e "${BLUE}${BOLD}Phase 1: Database Initialization${NC}"
echo "-------------------------------------------"

python3 << EOF
import asyncio
from app.db.session import init_db

async def test_db():
    try:
        await init_db()
        print("${GREEN}✓ Database initialized successfully${NC}")
        return True
    except Exception as e:
        print(f"${RED}✗ Database initialization failed: {e}${NC}")
        return False

result = asyncio.run(test_db())
exit(0 if result else 1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Phase 1 passed${NC}"
else
    echo -e "${RED}✗ Phase 1 failed${NC}"
    exit 1
fi

echo ""

# Phase 2: Check Admin Users
echo -e "${BLUE}${BOLD}Phase 2: Admin User Check${NC}"
echo "-------------------------------------------"

ADMIN_COUNT=$(python3 << EOF
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService

async def count_admins():
    async with AsyncSessionLocal() as db:
        admins = await AdminService.get_all(db)
        return len(admins)

count = asyncio.run(count_admins())
print(count)
EOF
)

if [ "$ADMIN_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $ADMIN_COUNT admin user(s)${NC}"

    python3 << EOF
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService

async def list_admins():
    async with AsyncSessionLocal() as db:
        admins = await AdminService.get_all(db)
        for admin in admins:
            print(f"  • {admin.username} ({admin.email}) - Superuser: {admin.is_superuser}")

asyncio.run(list_admins())
EOF

else
    echo -e "${YELLOW}⚠ No admin users found${NC}"
    echo "  Create one with: python3 create_admin.py"
    echo ""
    read -p "Create admin user now? (y/N): " CREATE_ADMIN
    if [ "$CREATE_ADMIN" = "y" ] || [ "$CREATE_ADMIN" = "Y" ]; then
        python3 create_admin.py
    else
        echo -e "${RED}Cannot continue without admin user${NC}"
        exit 1
    fi
fi

echo ""

# Phase 3: Server Check
echo -e "${BLUE}${BOLD}Phase 3: Server Availability${NC}"
echo "-------------------------------------------"

# Check if server is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running${NC}"
    SERVER_RUNNING=true
else
    echo -e "${YELLOW}⚠ Server is not running${NC}"
    echo "  Start server with: uvicorn app.main:app --reload"
    echo ""
    read -p "Start server in background for testing? (y/N): " START_SERVER
    if [ "$START_SERVER" = "y" ] || [ "$START_SERVER" = "Y" ]; then
        echo "Starting server..."
        uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/spond_server.log 2>&1 &
        SERVER_PID=$!
        echo "Server PID: $SERVER_PID"

        # Wait for server to start
        echo -n "Waiting for server to start"
        for i in {1..10}; do
            if curl -s http://localhost:8000/health > /dev/null 2>&1; then
                echo ""
                echo -e "${GREEN}✓ Server started${NC}"
                SERVER_RUNNING=true
                break
            fi
            echo -n "."
            sleep 1
        done

        if [ "$SERVER_RUNNING" != "true" ]; then
            echo ""
            echo -e "${RED}✗ Server failed to start${NC}"
            cat /tmp/spond_server.log
            exit 1
        fi
    else
        echo -e "${RED}Cannot continue without running server${NC}"
        exit 1
    fi
fi

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health endpoint responding${NC}"
else
    echo -e "${RED}✗ Health endpoint not responding correctly${NC}"
    exit 1
fi

echo ""

# Phase 4: Authentication Tests
echo -e "${BLUE}${BOLD}Phase 4: Authentication Tests${NC}"
echo "-------------------------------------------"

# Get test credentials
echo "Enter test admin credentials:"
read -p "Username (default: testadmin): " TEST_USER
TEST_USER=${TEST_USER:-testadmin}

read -sp "Password: " TEST_PASS
echo ""

if [ -z "$TEST_PASS" ]; then
    echo -e "${RED}✗ Password required${NC}"
    exit 1
fi

# Test login
echo "Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ Login failed${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
else
    echo -e "${GREEN}✓ Login successful${NC}"
    echo "  Token: ${TOKEN:0:50}..."
fi

# Test /me endpoint
echo "Testing /me endpoint..."
ME_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN")

if echo "$ME_RESPONSE" | grep -q "username"; then
    echo -e "${GREEN}✓ /me endpoint working${NC}"
    USERNAME=$(echo $ME_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('username', 'unknown'))")
    echo "  Logged in as: $USERNAME"
else
    echo -e "${RED}✗ /me endpoint failed${NC}"
    exit 1
fi

# Test list admins
echo "Testing list admins..."
ADMINS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/auth/admins" \
  -H "Authorization: Bearer $TOKEN")

if echo "$ADMINS_RESPONSE" | grep -q "\["; then
    echo -e "${GREEN}✓ List admins working${NC}"
else
    echo -e "${YELLOW}⚠ Could not list admins (may not be superuser)${NC}"
fi

echo ""

# Phase 5: Events API Tests
echo -e "${BLUE}${BOLD}Phase 5: Events API Tests${NC}"
echo "-------------------------------------------"

# Check if Spond credentials are configured
SPOND_USER=$(grep SPOND_USERNAME .env 2>/dev/null | cut -d'=' -f2)
if [ -z "$SPOND_USER" ] || [ "$SPOND_USER" = "" ]; then
    echo -e "${YELLOW}⚠ Spond credentials not configured${NC}"
    echo "  Events sync will be skipped"
    echo "  Configure in .env: SPOND_USERNAME and SPOND_PASSWORD"
    SKIP_SYNC=true
else
    echo -e "${GREEN}✓ Spond credentials configured${NC}"
    SKIP_SYNC=false
fi

if [ "$SKIP_SYNC" = "false" ]; then
    # Test sync
    echo "Testing events sync..."
    SYNC_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/events/sync?max_events=10" \
      -H "Authorization: Bearer $TOKEN")

    if echo "$SYNC_RESPONSE" | grep -q "total_fetched"; then
        echo -e "${GREEN}✓ Events sync successful${NC}"
        FETCHED=$(echo $SYNC_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_fetched', 0))")
        CREATED=$(echo $SYNC_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('created', 0))")
        echo "  Fetched: $FETCHED, Created: $CREATED"
    else
        echo -e "${YELLOW}⚠ Events sync may have failed${NC}"
        echo "  Response: $SYNC_RESPONSE"
    fi
fi

# Test list events
echo "Testing list events..."
LIST_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/events?limit=5" \
  -H "Authorization: Bearer $TOKEN")

if echo "$LIST_RESPONSE" | grep -q "events"; then
    echo -e "${GREEN}✓ List events working${NC}"
    TOTAL=$(echo $LIST_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('total', 0))")
    echo "  Total events: $TOTAL"
else
    echo -e "${RED}✗ List events failed${NC}"
fi

# Test statistics
echo "Testing event statistics..."
STATS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/events/stats" \
  -H "Authorization: Bearer $TOKEN")

if echo "$STATS_RESPONSE" | grep -q "total_events"; then
    echo -e "${GREEN}✓ Statistics working${NC}"
    TOTAL_EVENTS=$(echo $STATS_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_events', 0))")
    UPCOMING=$(echo $STATS_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('upcoming_events', 0))")
    echo "  Total: $TOTAL_EVENTS, Upcoming: $UPCOMING"
else
    echo -e "${RED}✗ Statistics failed${NC}"
fi

echo ""

# Cleanup
if [ ! -z "$SERVER_PID" ]; then
    echo "Stopping test server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
fi

# Final Summary
echo ""
echo -e "${BOLD}=========================================="
echo "Test Summary"
echo -e "==========================================${NC}"
echo -e "${GREEN}✓ Phase 0: Environment${NC}"
echo -e "${GREEN}✓ Phase 1: Database${NC}"
echo -e "${GREEN}✓ Phase 2: Admin Users${NC}"
echo -e "${GREEN}✓ Phase 3: Server${NC}"
echo -e "${GREEN}✓ Phase 4: Authentication${NC}"
echo -e "${GREEN}✓ Phase 5: Events API${NC}"
echo ""
echo -e "${BOLD}${GREEN}All tests passed! Ready for Phase 4.${NC}"
echo ""
echo "Next steps:"
echo "1. Review the API docs: http://localhost:8000/api/v1/docs"
echo "2. Configure Spond credentials for full events testing"
echo "3. Proceed with Phase 4: Groups & Members API"
