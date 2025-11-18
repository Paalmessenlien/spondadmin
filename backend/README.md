# Spond Admin API - Backend

FastAPI-based backend for the Spond administration interface.

## Features

- **FastAPI** - Modern, async Python web framework
- **SQLAlchemy** - Async ORM for database operations
- **Alembic** - Database migrations
- **Spond Integration** - Full integration with Spond API using `spond` and `spond-classes` libraries
- **JWT Authentication** - Secure admin authentication
- **Pydantic** - Data validation and settings management

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

## Installation

1. **Install Python virtual environment package** (if not already installed):
   ```bash
   sudo apt install python3-venv
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure:
   - `SECRET_KEY` - Generate using: `openssl rand -hex 32`
   - `SPOND_USERNAME` - Your Spond account email
   - `SPOND_PASSWORD` - Your Spond account password
   - Other settings as needed

5. **Initialize database**:
   ```bash
   # The database will be created automatically on first run
   # Or you can use Alembic migrations:
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

6. **Create the first admin user**:
   ```bash
   python3 create_admin.py
   ```

   Follow the prompts to create your first admin user (superuser recommended).

## Running the Server

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── core/
│   │   ├── config.py        # Configuration settings
│   │   ├── security.py      # Auth utilities (JWT, passwords)
│   │   └── deps.py          # FastAPI dependencies
│   ├── db/
│   │   ├── base.py          # SQLAlchemy base
│   │   └── session.py       # Database session management
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── admin.py
│   │   ├── event.py
│   │   ├── group.py
│   │   ├── member.py
│   │   ├── sync_history.py
│   │   └── audit_log.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── admin.py         # Admin schemas
│   │   └── token.py         # Token schemas
│   ├── services/            # Business logic
│   │   ├── admin_service.py # Admin CRUD operations
│   │   └── spond_service.py # Spond API wrapper
│   └── api/v1/              # API routes
│       └── auth.py          # Authentication endpoints
├── alembic/                 # Database migrations
├── create_admin.py          # Admin user creation script
├── test_auth.sh             # Authentication test script
├── requirements.txt
├── .env.example
├── .env
└── README.md
```

## Database Models

- **Admin** - Admin users with authentication
- **Event** - Cached Spond events
- **Group** - Cached Spond groups
- **Member** - Cached Spond members
- **SyncHistory** - Track API synchronization
- **AuditLog** - Track admin actions

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

## Testing Authentication

### Using the Test Script

```bash
./test_auth.sh
```

This script tests the authentication endpoints including login, get current user, and token validation.

### Manual Testing with curl

1. **Login**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"yourusername","password":"yourpassword"}'
   ```

2. **Get current user** (replace TOKEN with the access_token from login):
   ```bash
   curl -X GET "http://localhost:8000/api/v1/auth/me" \
     -H "Authorization: Bearer TOKEN"
   ```

3. **List all admins** (superuser only):
   ```bash
   curl -X GET "http://localhost:8000/api/v1/auth/admins" \
     -H "Authorization: Bearer TOKEN"
   ```

## Development

### Adding New Database Models

1. Create model in `app/models/`
2. Import in `app/models/__init__.py`
3. Import in `alembic/env.py`
4. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Add new model"
   alembic upgrade head
   ```

### Adding New API Endpoints

1. Create Pydantic schemas in `app/schemas/`
2. Create router in `app/api/v1/`
3. Include router in `app/main.py`

## Implementation Status

### Completed ✅

**Phase 1: Backend Foundation**
- ✅ Project structure and configuration
- ✅ Database models (Admin, Event, Group, Member, SyncHistory, AuditLog)
- ✅ Database connection and session management
- ✅ Spond API service wrapper

**Phase 2: Authentication System**
- ✅ Pydantic schemas for authentication
- ✅ Admin CRUD service
- ✅ JWT authentication and security utilities
- ✅ Authentication API endpoints (login, user management)
- ✅ Admin user creation script

**Phase 3: Events API**
- ✅ Event Pydantic schemas
- ✅ Event sync service (sync from Spond API)
- ✅ Event CRUD service
- ✅ List events with filtering (date range, type, status)
- ✅ Get event details with responses
- ✅ Update event information
- ✅ Export attendance reports (Excel)
- ✅ Manage event responses
- ✅ Event statistics

### To Be Implemented 📋

**Phase 4: Groups API** (`app/api/v1/groups.py`)
- List all groups
- Get group details with members, roles, subgroups
- Member filtering by role/subgroup

**Phase 5: Members API** (`app/api/v1/members.py`)
- Search and filter members
- Get member details and profiles
- View participation history

**Phase 6: Sync Service**
- Background synchronization with Spond API
- Scheduled jobs using APScheduler
- Cache management and refresh logic

## License

This project uses the Spond API through the unofficial `spond` and `spond-classes` libraries (GPL-3.0).
