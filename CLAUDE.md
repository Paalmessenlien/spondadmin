# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spond Admin Interface - A full-stack web application for managing Spond events, groups, and members. The system syncs data from the Spond API and provides administrative capabilities with analytics dashboards.

## Commands

### Backend (FastAPI)

```bash
cd backend
source venv/bin/activate

# Start development server
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Create admin user
python3 create_admin.py

# Reset admin password
python3 reset_admin_password.py
```

### Frontend (Nuxt 3)

```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build
```

### Kill Stale Processes

```bash
lsof -ti:8001 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

## Architecture

### Backend (`backend/`)

- **Framework**: FastAPI with async SQLAlchemy ORM
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Auth**: JWT tokens with bcrypt password hashing
- **External API**: Spond API via `spond` and `spond-classes` libraries

**Key Directories**:
- `app/api/v1/` - API route handlers (auth, events, groups, members, analytics, scheduler)
- `app/services/` - Business logic and Spond sync services
- `app/models/` - SQLAlchemy ORM models
- `app/schemas/` - Pydantic validation schemas
- `app/core/` - Config (`config.py`), security (`security.py`), dependencies (`deps.py`)

**Sync Architecture**: Each entity (events, groups, members) has paired services:
- `*_service.py` - CRUD operations
- `*_sync_service.py` - Spond API synchronization

**Background Jobs**: APScheduler runs automatic syncs at configurable intervals (see `.env.example`).

### Frontend (`frontend/`)

- **Framework**: Nuxt 3 with Vue 3
- **UI**: Nuxt UI v3 with Tailwind CSS v4
- **State**: Pinia stores
- **Charts**: Chart.js with vue-chartjs

**Key Directories**:
- `pages/dashboard/` - Main app pages (events/, groups/, members/, analytics.vue)
- `components/` - Reusable Vue components (charts, empty states, breadcrumbs)
- `stores/` - Pinia state management
- `layouts/` - Page layouts (dashboard.vue)
- `middleware/` - Auth middleware

**Routing Pattern**: List pages use `pages/dashboard/{entity}/index.vue`, detail pages use `pages/dashboard/{entity}/[id].vue`.

### Data Flow

1. Spond API → Sync Services → SQLite/PostgreSQL
2. Frontend → Backend API → Database
3. Background scheduler refreshes data automatically

## Configuration

Backend config via `backend/.env` (copy from `.env.example`):
- `SPOND_USERNAME` / `SPOND_PASSWORD` - Spond API credentials
- `SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)
- `AUTO_SYNC_ENABLED` - Enable background sync
- `SYNC_*_INTERVAL_MINUTES` - Sync frequency per entity

Frontend config via `frontend/.env`:
- `NUXT_PUBLIC_API_BASE` - Backend API URL (default: `http://localhost:8001/api/v1`)

## API Endpoints

Base URL: `http://localhost:8001/api/v1`

- `/auth/login` - JWT authentication
- `/events/`, `/events/sync`, `/events/{id}` - Event management
- `/groups/`, `/groups/sync`, `/groups/{id}` - Group management
- `/members/`, `/members/sync`, `/members/{id}` - Member management
- `/analytics/summary`, `/analytics/attendance-trends`, `/analytics/response-rates` - Analytics
- `/scheduler/status`, `/scheduler/jobs` - Background job management
- `/docs` - Swagger UI

## Important Patterns

**Timestamp Handling**: SQLAlchemy models use `TimestampMixin`. When creating records via sync services, explicitly set `created_at` and `updated_at` fields for SQLite compatibility.

**Analytics Response Format**: Event responses are stored as JSON with structure `{"responses": [...], "accepted_uids": [...]}`. The `analytics_service.py` uses `_get_responses_array()` helper for backward compatibility.

**Nuxt UI CSS**: The `assets/css/main.css` must contain both `@import "tailwindcss"` and `@import "@nuxt/ui"` for proper styling.

**NuxtPage Key**: `app.vue` uses `<NuxtPage :key="$route.fullPath" />` to force re-renders on route changes.
