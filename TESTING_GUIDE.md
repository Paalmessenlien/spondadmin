# Complete Testing Guide

This guide will walk you through testing all completed phases of the Spond Admin API.

## Prerequisites Setup

### 1. Install System Packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-full
```

### 2. Create Virtual Environment

```bash
cd /home/paal/spond/backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

You should see output installing all packages (FastAPI, SQLAlchemy, etc.).

## Phase 1: Backend Foundation Test

### Verify Project Structure

```bash
# Check that all directories exist
ls -la app/
ls -la app/models/
ls -la app/services/
ls -la app/api/v1/
ls -la alembic/
```

Expected: All directories should exist with Python files inside.

### Verify Configuration

```bash
# Check .env file exists
cat .env | grep -E "SECRET_KEY|DATABASE_URL"
```

Expected: Should show SECRET_KEY and DATABASE_URL settings.

### Test Database Connection

```bash
# Try to import the app (this will create the database)
python3 -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"
```

Expected: No errors, creates `spond_admin.db` file.

```bash
# Verify database file exists
ls -lh spond_admin.db
```

Expected: Database file should exist (may be 0 bytes initially).

## Phase 2: Authentication System Test

### Step 1: Create Admin User

```bash
# Run the admin creation script
python3 create_admin.py
```

**Inputs:**
- Username: `testadmin`
- Email: `test@example.com`
- Full Name: `Test Admin`
- Password: `testpassword123`
- Is superuser: `y`

Expected output:
```
✓ Admin user created successfully!

  Username: testadmin
  Email: test@example.com
  Full Name: Test Admin
  Superuser: Yes
  Active: Yes
```

### Step 2: Verify Admin in Database

```bash
# Check admin was created
python3 -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService

async def check():
    async with AsyncSessionLocal() as db:
        admins = await AdminService.get_all(db)
        for admin in admins:
            print(f'- {admin.username} ({admin.email}) - Superuser: {admin.is_superuser}')

asyncio.run(check())
"
```

Expected: Should list your admin user.

### Step 3: Start the Server

```bash
# In one terminal, start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
Starting up Spond Admin API...
Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Keep this terminal open!**

### Step 4: Test Health Endpoint

In a **new terminal**:

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status":"healthy","service":"Spond Admin API","version":"1.0.0"}
```

### Step 5: Test API Documentation

```bash
# Check if Swagger UI is accessible
curl -s http://localhost:8000/api/v1/docs | grep -o "<title>.*</title>"
```

Expected: Should return HTML title with "FastAPI".

Or open in browser: http://localhost:8000/api/v1/docs

### Step 6: Test Authentication Endpoints

```bash
cd /home/paal/spond/backend
./test_auth.sh
```

**When prompted:**
- Make sure server is running
- Press Enter to continue

Expected output:
```
Test 1: Login
-------------------------------------------
✓ Login successful

Test 2: Get Current User Info
-------------------------------------------
✓ Successfully retrieved user info

Test 3: List All Admins (Superuser only)
-------------------------------------------
✓ Successfully retrieved admins list

Test 4: Test Invalid Token
-------------------------------------------
✓ Invalid token correctly rejected
```

### Step 7: Manual Authentication Test

```bash
# Login and get token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testadmin","password":"testpassword123"}' | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token: ${TOKEN:0:50}..."

# Test /me endpoint
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Should return your user information in JSON format.

### Step 8: Test Admin Management

```bash
# Create another admin user (using the token from previous step)
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "regularuser",
    "email": "regular@example.com",
    "password": "password123",
    "full_name": "Regular User",
    "is_superuser": false,
    "is_active": true
  }' | python3 -m json.tool
```

Expected: Should return the created user without password field.

```bash
# List all admins
curl -X GET "http://localhost:8000/api/v1/auth/admins" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Should list 2 admins (testadmin and regularuser).

## Phase 3: Events API Test

### Step 1: Configure Spond Credentials

**Important:** You need valid Spond credentials for this section.

```bash
# Edit .env file
nano .env
```

Add your credentials:
```
SPOND_USERNAME=your-spond-email@example.com
SPOND_PASSWORD=your-spond-password
```

Save and exit (Ctrl+X, Y, Enter).

**Restart the server** for changes to take effect:
- Stop the server (Ctrl+C in the server terminal)
- Start again: `uvicorn app.main:app --reload`

### Step 2: Get Fresh Token

```bash
# Login again
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testadmin","password":"testpassword123"}' | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token ready!"
```

### Step 3: Sync Events from Spond

```bash
# Sync events
curl -X POST "http://localhost:8000/api/v1/events/sync?max_events=50" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected output (if credentials are correct):
```json
{
  "total_fetched": 45,
  "created": 45,
  "updated": 0,
  "errors": 0,
  "sync_time": "2025-01-16T..."
}
```

If you get errors, check:
- Spond credentials are correct
- You have access to Spond events
- Network connection is working

### Step 4: List Events

```bash
# List first 5 events
curl -X GET "http://localhost:8000/api/v1/events?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: JSON with events array and total count.

### Step 5: Get Event Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/events/stats" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected output:
```json
{
  "total_events": 45,
  "upcoming_events": 12,
  "past_events": 33,
  "cancelled_events": 2,
  "events_by_type": {
    "EVENT": 30,
    "AVAILABILITY": 10,
    "RECURRING": 5
  }
}
```

### Step 6: Test Event Filtering

```bash
# Filter by event type
curl -X GET "http://localhost:8000/api/v1/events?event_type=EVENT&limit=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Search events
curl -X GET "http://localhost:8000/api/v1/events?search=practice&limit=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Filter by date
curl -X GET "http://localhost:8000/api/v1/events?start_date=2025-01-01T00:00:00&limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Filtered results matching the criteria.

### Step 7: Get Specific Event

```bash
# Get the ID of first event
EVENT_ID=$(curl -s -X GET "http://localhost:8000/api/v1/events?limit=1" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data['events'][0]['id'] if data['events'] else 'none')")

echo "Event ID: $EVENT_ID"

# Get event details
curl -X GET "http://localhost:8000/api/v1/events/$EVENT_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: Complete event details including responses.

### Step 8: Update Event

```bash
# Update event heading and description
curl -X PUT "http://localhost:8000/api/v1/events/$EVENT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "heading": "Updated Event Title",
    "description": "This was updated via API"
  }' | python3 -m json.tool
```

Expected: Updated event data returned.

### Step 9: Run Automated Event Tests

```bash
./test_events.sh
```

Expected: All tests should pass if Spond credentials are configured.

### Step 10: Test Attendance Export (Optional)

```bash
# Export attendance for an event
curl -X GET "http://localhost:8000/api/v1/events/$EVENT_ID/attendance" \
  -H "Authorization: Bearer $TOKEN" \
  --output "attendance_export.xlsx"

# Check file was created
ls -lh attendance_export.xlsx
```

Expected: Excel file should be downloaded.

## Complete Test Summary

Run this command to execute all tests:

```bash
cd /home/paal/spond/backend

echo "=========================================="
echo "Running Complete Test Suite"
echo "=========================================="
echo ""

# 1. Check environment
echo "1. Checking Python environment..."
python3 --version

echo "2. Checking virtual environment..."
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
else
    echo "✗ Virtual environment missing - create with: python3 -m venv venv"
fi

echo "3. Checking database..."
if [ -f "spond_admin.db" ]; then
    echo "✓ Database exists"
    ls -lh spond_admin.db
else
    echo "✗ Database missing - will be created on first run"
fi

echo "4. Checking configuration..."
if [ -f ".env" ]; then
    echo "✓ .env file exists"
else
    echo "✗ .env file missing"
fi

echo ""
echo "To run full tests:"
echo "1. source venv/bin/activate"
echo "2. uvicorn app.main:app --reload"
echo "3. In another terminal: ./test_auth.sh"
echo "4. If Spond credentials configured: ./test_events.sh"
echo ""
echo "Or visit http://localhost:8000/api/v1/docs for interactive testing"
```

## Troubleshooting

### Server won't start

Check logs for errors:
```bash
uvicorn app.main:app --reload --log-level debug
```

### Authentication fails

Verify admin user exists:
```bash
python3 create_admin.py
```

### Events sync fails

Check Spond credentials:
```bash
cat .env | grep SPOND
```

Verify credentials are correct in Spond web interface.

### Database errors

Delete and recreate database:
```bash
rm spond_admin.db
uvicorn app.main:app --reload
```

## Success Criteria

✅ **Phase 1**: Database created, configuration loaded
✅ **Phase 2**: Admin user created, login works, token valid
✅ **Phase 3**: Events sync from Spond, filtering works, statistics accurate

All tests passing = Ready for Phase 4!
