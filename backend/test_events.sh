#!/bin/bash

# Test script for events API endpoints
# Make sure the server is running before executing this script
# Make sure you have configured Spond credentials in .env

BASE_URL="http://localhost:8000/api/v1"

echo "=========================================="
echo "Spond Admin API - Events Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test data
USERNAME="testadmin"
PASSWORD="testpassword123"

echo "${YELLOW}Note: Make sure you have:${NC}"
echo "1. Created an admin user (python3 create_admin.py)"
echo "2. Configured Spond credentials in .env"
echo "3. Server is running (uvicorn app.main:app --reload)"
echo ""
read -p "Press Enter to continue with the test..."
echo ""

# Step 1: Login
echo "${BLUE}Step 1: Login${NC}"
echo "-------------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "${RED}✗ Login failed - No token received${NC}"
  echo "Response: $LOGIN_RESPONSE"
  echo ""
  exit 1
else
  echo "${GREEN}✓ Login successful${NC}"
  echo "Token: ${TOKEN:0:50}..."
  echo ""
fi

# Step 2: Sync events from Spond
echo "${BLUE}Step 2: Sync Events from Spond API${NC}"
echo "-------------------------------------------"
SYNC_RESPONSE=$(curl -s -X POST "$BASE_URL/events/sync?max_events=50" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $SYNC_RESPONSE"

if echo "$SYNC_RESPONSE" | grep -q "total_fetched"; then
  FETCHED=$(echo $SYNC_RESPONSE | grep -o '"total_fetched":[0-9]*' | cut -d':' -f2)
  CREATED=$(echo $SYNC_RESPONSE | grep -o '"created":[0-9]*' | cut -d':' -f2)
  UPDATED=$(echo $SYNC_RESPONSE | grep -o '"updated":[0-9]*' | cut -d':' -f2)

  echo "${GREEN}✓ Sync successful${NC}"
  echo "  Fetched: $FETCHED"
  echo "  Created: $CREATED"
  echo "  Updated: $UPDATED"
else
  echo "${YELLOW}⚠ Sync may have failed (check Spond credentials)${NC}"
fi
echo ""

# Step 3: List events
echo "${BLUE}Step 3: List Events${NC}"
echo "-------------------------------------------"
LIST_RESPONSE=$(curl -s -X GET "$BASE_URL/events?limit=5" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: ${LIST_RESPONSE:0:500}..."

if echo "$LIST_RESPONSE" | grep -q "events"; then
  TOTAL=$(echo $LIST_RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
  echo "${GREEN}✓ Successfully retrieved events${NC}"
  echo "  Total events: $TOTAL"
else
  echo "${RED}✗ Failed to retrieve events${NC}"
fi
echo ""

# Step 4: Get event statistics
echo "${BLUE}Step 4: Get Event Statistics${NC}"
echo "-------------------------------------------"
STATS_RESPONSE=$(curl -s -X GET "$BASE_URL/events/stats" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $STATS_RESPONSE"

if echo "$STATS_RESPONSE" | grep -q "total_events"; then
  echo "${GREEN}✓ Successfully retrieved statistics${NC}"
else
  echo "${RED}✗ Failed to retrieve statistics${NC}"
fi
echo ""

# Step 5: Get specific event (if events exist)
if [ ! -z "$TOTAL" ] && [ "$TOTAL" -gt 0 ]; then
  echo "${BLUE}Step 5: Get Specific Event${NC}"
  echo "-------------------------------------------"

  # Extract first event ID from list
  EVENT_ID=$(echo $LIST_RESPONSE | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

  if [ ! -z "$EVENT_ID" ]; then
    EVENT_RESPONSE=$(curl -s -X GET "$BASE_URL/events/$EVENT_ID" \
      -H "Authorization: Bearer $TOKEN")

    echo "Response: ${EVENT_RESPONSE:0:300}..."

    if echo "$EVENT_RESPONSE" | grep -q "heading"; then
      HEADING=$(echo $EVENT_RESPONSE | grep -o '"heading":"[^"]*' | cut -d'"' -f4)
      echo "${GREEN}✓ Successfully retrieved event${NC}"
      echo "  Event: $HEADING"
    else
      echo "${RED}✗ Failed to retrieve event${NC}"
    fi
  fi
  echo ""
fi

# Step 6: Test filtering
echo "${BLUE}Step 6: Test Event Filtering${NC}"
echo "-------------------------------------------"
FILTER_RESPONSE=$(curl -s -X GET "$BASE_URL/events?event_type=EVENT&limit=3" \
  -H "Authorization: Bearer $TOKEN")

if echo "$FILTER_RESPONSE" | grep -q "events"; then
  echo "${GREEN}✓ Filtering works${NC}"
  echo "Response: ${FILTER_RESPONSE:0:200}..."
else
  echo "${YELLOW}⚠ Filtering may have issues${NC}"
fi
echo ""

# Step 7: Test search
echo "${BLUE}Step 7: Test Event Search${NC}"
echo "-------------------------------------------"
SEARCH_RESPONSE=$(curl -s -X GET "$BASE_URL/events?search=practice&limit=3" \
  -H "Authorization: Bearer $TOKEN")

if echo "$SEARCH_RESPONSE" | grep -q "events"; then
  echo "${GREEN}✓ Search works${NC}"
  echo "Response: ${SEARCH_RESPONSE:0:200}..."
else
  echo "${YELLOW}⚠ Search may have issues${NC}"
fi
echo ""

echo "=========================================="
echo "Events API Tests Complete"
echo "=========================================="
echo ""
echo "${YELLOW}Next Steps:${NC}"
echo "1. Visit http://localhost:8000/api/v1/docs to explore all endpoints"
echo "2. Try updating an event"
echo "3. Try exporting attendance for an event"
echo "4. Configure filters for specific date ranges"
