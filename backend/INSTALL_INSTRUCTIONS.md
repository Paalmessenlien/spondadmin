# Installation & Testing Instructions

## Required System Package

Before running tests, you need to install the Python venv package:

```bash
sudo apt install python3.13-venv
```

## Quick Setup & Test

After installing `python3.13-venv`, run:

```bash
cd /home/paal/spond/backend

# Remove old venv if exists
rm -rf venv

# Create fresh virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create admin user
python3 create_admin.py
```

**When creating admin user:**
- Username: `testadmin`
- Email: `test@example.com`
- Password: `testpassword123`
- Superuser: `y`

## Run Tests

### Terminal 1: Start Server

```bash
cd /home/paal/spond/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Terminal 2: Run Tests

```bash
cd /home/paal/spond/backend
source venv/bin/activate

# Test authentication
./test_auth.sh

# If you have Spond credentials, test events:
# 1. Edit .env and add SPOND_USERNAME and SPOND_PASSWORD
# 2. Restart the server
# 3. Run: ./test_events.sh
```

## Complete Automated Test

```bash
cd /home/paal/spond/backend
source venv/bin/activate
./run_all_tests.sh
```

This will test:
- Environment setup
- Database initialization
- Admin user creation
- Authentication API
- Events API (if Spond credentials configured)

## API Documentation

Once the server is running, visit:

**Swagger UI**: http://localhost:8000/api/v1/docs

You can test all endpoints interactively from the browser!

## Testing Without Spond Credentials

If you don't have Spond credentials yet, you can still test:

✅ Authentication system (login, user management)
✅ Database operations
✅ API documentation
✅ Server health

❌ Event synchronization (requires Spond account)
❌ Event listing/filtering (requires synced events)
❌ Attendance export (requires synced events)

The authentication system works completely independently!

## Quick Verification

After setup, run these commands to verify everything works:

```bash
# 1. Check server health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"Spond Admin API","version":"1.0.0"}

# 2. Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testadmin","password":"testpassword123"}'

# Should return a JWT token

# 3. Check API docs
# Visit: http://localhost:8000/api/v1/docs
```

## Next Steps After Testing

Once all tests pass:
- ✅ Proceed to Phase 4 (Groups & Members API)
- ✅ Start frontend development with Nuxt
- ✅ Deploy to production (with security hardening)
