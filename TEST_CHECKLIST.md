# Testing Checklist - Spond Admin API

Complete this checklist to verify all phases are working correctly.

## Prerequisites ✓

- [ ] Python 3.10+ installed
- [ ] `python3-venv` package installed (`sudo apt install python3-venv`)
- [ ] Git repository cloned

## Quick Start (Recommended)

```bash
cd /home/paal/spond/backend
./setup_and_test.sh
```

This script will:
1. Create virtual environment
2. Install dependencies
3. Initialize database
4. Create admin user
5. Guide you through testing

## Manual Testing Checklist

### Phase 1: Backend Foundation ✓

#### Environment Setup

```bash
cd /home/paal/spond/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

- [ ] Virtual environment created successfully
- [ ] All dependencies installed without errors
- [ ] `uvicorn` command available

#### Configuration

```bash
# Check .env exists
cat .env
```

- [ ] `.env` file exists
- [ ] SECRET_KEY is set (not default)
- [ ] DATABASE_URL is configured

#### Project Structure

```bash
# Verify all directories
ls -la app/{models,services,api/v1,core,db,schemas}
```

- [ ] All directories exist
- [ ] Python files present in each directory

### Phase 2: Authentication System ✓

#### Database Initialization

```bash
# Initialize database
python3 -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"

# Verify database file
ls -lh spond_admin.db
```

- [ ] Database created without errors
- [ ] `spond_admin.db` file exists

#### Create Admin User

```bash
python3 create_admin.py
```

**Test Credentials:**
- Username: `testadmin`
- Password: `testpassword123`
- Superuser: Yes

- [ ] Admin user created successfully
- [ ] User details displayed correctly

#### Verify Admin in Database

```bash
python3 << 'EOF'
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService

async def check():
    async with AsyncSessionLocal() as db:
        admins = await AdminService.get_all(db)
        for admin in admins:
            print(f'{admin.username} - {admin.email}')

asyncio.run(check())
EOF
```

- [ ] Admin user appears in list
- [ ] Email and username correct

#### Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
Starting up Spond Admin API...
Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

- [ ] Server starts without errors
- [ ] "Database initialized" message shown
- [ ] Server listening on port 8000

#### Test Endpoints (New Terminal)

```bash
# Health check
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/api/v1/docs
```

- [ ] Health endpoint returns JSON with "healthy"
- [ ] API docs page accessible (returns HTML)

#### Run Authentication Tests

```bash
./test_auth.sh
```

Expected: All 4 tests pass ✓

- [ ] Test 1: Login successful
- [ ] Test 2: Get current user info works
- [ ] Test 3: List admins works (if superuser)
- [ ] Test 4: Invalid token rejected

#### Manual Auth Test

```bash
# Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testadmin","password":"testpassword123"}' | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token: ${TOKEN:0:50}..."

# Get user info
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

- [ ] Token received
- [ ] User info returned with correct username/email

#### Test Admin Management

```bash
# Create second admin
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

# List all admins
curl -X GET "http://localhost:8000/api/v1/auth/admins" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

- [ ] Second admin created successfully
- [ ] List shows 2 admins
- [ ] Password not included in response

### Phase 3: Events API ✓

#### Configure Spond Credentials

```bash
nano .env
```

Add:
```
SPOND_USERNAME=your-email@example.com
SPOND_PASSWORD=your-password
```

**Restart the server after editing .env**

- [ ] Spond credentials added to .env
- [ ] Server restarted

#### Get Fresh Token

```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testadmin","password":"testpassword123"}' | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
```

- [ ] Token obtained

#### Test Event Sync

```bash
curl -X POST "http://localhost:8000/api/v1/events/sync?max_events=50" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected response:
```json
{
  "total_fetched": 45,
  "created": 45,
  "updated": 0,
  "errors": 0,
  "sync_time": "2025-01-16T..."
}
```

- [ ] Sync successful (no errors)
- [ ] Events fetched from Spond
- [ ] `total_fetched` > 0

**If sync fails:**
- Verify Spond credentials are correct
- Check you have access to Spond events
- Test logging in at https://spond.com

#### Test List Events

```bash
curl -X GET "http://localhost:8000/api/v1/events?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

- [ ] Events list returned
- [ ] `total` field shows count
- [ ] Events array contains event objects

#### Test Event Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/events/stats" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

- [ ] Statistics returned
- [ ] Shows total_events, upcoming_events, past_events
- [ ] Shows events_by_type breakdown

#### Test Event Filtering

```bash
# By type
curl -X GET "http://localhost:8000/api/v1/events?event_type=EVENT&limit=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# By search
curl -X GET "http://localhost:8000/api/v1/events?search=practice&limit=3" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# By date
curl -X GET "http://localhost:8000/api/v1/events?start_date=2025-01-01T00:00:00" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

- [ ] Type filter works
- [ ] Search filter works
- [ ] Date filter works

#### Test Get Specific Event

```bash
# Get first event ID
EVENT_ID=$(curl -s -X GET "http://localhost:8000/api/v1/events?limit=1" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys,json; data=json.load(sys.stdin); print(data['events'][0]['id'] if data['events'] else 0)")

# Get event details
curl -X GET "http://localhost:8000/api/v1/events/$EVENT_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

- [ ] Event ID retrieved
- [ ] Event details returned
- [ ] Contains heading, description, responses, etc.

#### Test Update Event

```bash
curl -X PUT "http://localhost:8000/api/v1/events/$EVENT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "heading": "Updated via API Test",
    "description": "This event was updated during testing"
  }' | python3 -m json.tool
```

- [ ] Update successful
- [ ] Heading and description changed
- [ ] Response shows updated event

#### Test Attendance Export

```bash
curl -X GET "http://localhost:8000/api/v1/events/$EVENT_ID/attendance" \
  -H "Authorization: Bearer $TOKEN" \
  --output test_attendance.xlsx

ls -lh test_attendance.xlsx
```

- [ ] Excel file downloaded
- [ ] File size > 0 bytes
- [ ] Can open in Excel/LibreOffice (optional)

#### Run Automated Event Tests

```bash
./test_events.sh
```

Expected: All tests pass

- [ ] Login test passed
- [ ] Sync test passed
- [ ] List events passed
- [ ] Statistics passed
- [ ] Get event passed
- [ ] Filter test passed
- [ ] Search test passed

### Complete Test Suite

```bash
# Run all tests automatically
./run_all_tests.sh
```

This script tests:
- Phase 0: Environment check
- Phase 1: Database initialization
- Phase 2: Admin users
- Phase 3: Server availability
- Phase 4: Authentication
- Phase 5: Events API

- [ ] All phases pass
- [ ] No errors in output
- [ ] Summary shows all green checkmarks

## API Documentation Test

Visit in browser:
- http://localhost:8000/api/v1/docs

- [ ] Swagger UI loads
- [ ] Can see all endpoints
- [ ] Can authorize with token
- [ ] Can execute requests from UI

Test in Swagger UI:
1. Click "Authorize" button
2. Paste your token
3. Try executing `/api/v1/auth/me`
4. Try executing `/api/v1/events` (GET)

- [ ] Authorization works
- [ ] GET /auth/me returns user info
- [ ] GET /events returns event list

## Success Criteria

All checkboxes should be marked ✓

### Phase 1: Backend Foundation
- [x] Virtual environment created
- [x] Dependencies installed
- [x] Configuration loaded
- [x] Project structure verified

### Phase 2: Authentication
- [x] Database initialized
- [x] Admin user created
- [x] Server starts correctly
- [x] Health endpoint responds
- [x] Login works
- [x] Token authentication works
- [x] User management works

### Phase 3: Events API
- [x] Spond credentials configured
- [x] Events sync from Spond
- [x] List events works
- [x] Filtering works
- [x] Search works
- [x] Statistics work
- [x] Update events works
- [x] Attendance export works

## If Something Fails

### Dependencies won't install
```bash
# Make sure python3-venv is installed
sudo apt install python3-venv python3-full

# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database errors
```bash
# Delete and recreate
rm spond_admin.db
python3 -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"
```

### Server won't start
```bash
# Check for port conflicts
lsof -i :8000

# Run with debug
uvicorn app.main:app --reload --log-level debug
```

### Authentication fails
```bash
# Recreate admin user
python3 create_admin.py
```

### Events sync fails
```bash
# Verify credentials
cat .env | grep SPOND

# Test Spond login at https://spond.com
# Make sure credentials are correct
```

## After All Tests Pass

You are ready for:
✅ Phase 4: Groups & Members API
✅ Frontend development
✅ Production deployment (with additional security hardening)

## Quick Reference

### Start Development
```bash
cd /home/paal/spond/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Run Tests
```bash
# In another terminal
cd /home/paal/spond/backend
source venv/bin/activate
./run_all_tests.sh
```

### View API Docs
http://localhost:8000/api/v1/docs

### Create Admin User
```bash
python3 create_admin.py
```

### Test Authentication
```bash
./test_auth.sh
```

### Test Events
```bash
./test_events.sh
```
