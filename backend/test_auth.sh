#!/bin/bash

# Test script for authentication endpoints
# Make sure the server is running before executing this script

BASE_URL="http://localhost:8000/api/v1"

echo "=========================================="
echo "Spond Admin API - Authentication Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test data
USERNAME="testadmin"
PASSWORD="testpassword123"
EMAIL="testadmin@example.com"

echo "${YELLOW}Note: Make sure you have created an admin user first!${NC}"
echo "Run: python3 create_admin.py"
echo ""
read -p "Press Enter to continue with the test..."
echo ""

# Test 1: Login
echo "Test 1: Login"
echo "-------------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

echo "Response: $LOGIN_RESPONSE"

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "${RED}✗ Login failed - No token received${NC}"
  echo ""
  exit 1
else
  echo "${GREEN}✓ Login successful${NC}"
  echo "Token: ${TOKEN:0:50}..."
  echo ""
fi

# Test 2: Get current user info
echo "Test 2: Get Current User Info"
echo "-------------------------------------------"
ME_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $ME_RESPONSE"

if echo "$ME_RESPONSE" | grep -q "username"; then
  echo "${GREEN}✓ Successfully retrieved user info${NC}"
else
  echo "${RED}✗ Failed to get user info${NC}"
fi
echo ""

# Test 3: List all admins (requires superuser)
echo "Test 3: List All Admins (Superuser only)"
echo "-------------------------------------------"
ADMINS_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/admins" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $ADMINS_RESPONSE"

if echo "$ADMINS_RESPONSE" | grep -q "\["; then
  echo "${GREEN}✓ Successfully retrieved admins list${NC}"
else
  echo "${YELLOW}⚠ Could not retrieve admins (might not be superuser)${NC}"
fi
echo ""

# Test 4: Test invalid token
echo "Test 4: Test Invalid Token"
echo "-------------------------------------------"
INVALID_RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer invalid_token_here")

echo "Response: $INVALID_RESPONSE"

if echo "$INVALID_RESPONSE" | grep -q "detail"; then
  echo "${GREEN}✓ Invalid token correctly rejected${NC}"
else
  echo "${RED}✗ Invalid token was not rejected${NC}"
fi
echo ""

echo "=========================================="
echo "Authentication Tests Complete"
echo "=========================================="
