# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Spond Admin Interface - A full-stack web application for managing Spond events, groups, and members. The system syncs data from the Spond API and provides administrative capabilities with analytics dashboards.

## Commands

### Docker (Recommended)

```bash
# Development - starts db, backend (hot-reload), frontend (HMR)
docker compose up
docker compose up --build          # rebuild after dependency changes
docker compose down                # stop all services
docker compose logs -f backend     # tail backend logs

# Production
docker compose -f docker-compose.prod.yml up -d
./scripts/deploy.sh                # full deployment (backup, build, migrate, health check)

# Create admin user (Docker)
docker compose exec backend python3 create_admin.py

# Run migrations (Docker)
docker compose exec backend alembic upgrade head

# Database backup/restore (Docker)
./scripts/backup.sh
./scripts/restore.sh backups/<file>.dump
```

### Local Development (without Docker)

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
- **Database**: PostgreSQL (production + Docker dev) / SQLite (local dev)
- **Auth**: JWT tokens with bcrypt password hashing, role-based access (admin/editor/viewer)
- **External API**: Spond API via `spond` and `spond-classes` libraries
- **Scraping**: bueskyting.no competition results and records via crawl4ai

**Key Directories**:
- `app/api/v1/` - API route handlers (auth, events, groups, members, analytics, scheduler, scores, scraper, backups, migrations)
- `app/services/` - Business logic, Spond sync, backup, migration, and scraper services
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
- `pages/dashboard/` - Main app pages (events/, groups/, members/, analytics.vue, reports/, scores/, settings/)
- `components/` - Reusable Vue components (charts, empty states, breadcrumbs)
  - `components/reports/` - Report-specific table components with sorting/filtering
- `composables/` - Composable functions for shared logic (`useApi.ts`, `usePermissions.ts`)
- `stores/` - Pinia state management
- `layouts/` - Page layouts (dashboard.vue)
- `middleware/` - Auth middleware

**Routing Pattern**: List pages use `pages/dashboard/{entity}/index.vue`, detail pages use `pages/dashboard/{entity}/[id].vue`.

### Data Flow

1. Spond API → Sync Services → PostgreSQL
2. bueskyting.no → Scraper Service → PostgreSQL
3. Frontend → Backend API → Database
4. Background scheduler refreshes data automatically

### Docker Infrastructure

- `docker-compose.yml` - Development (db + backend + frontend, hot-reload)
- `docker-compose.prod.yml` - Production (+ nginx reverse proxy, resource limits, logging)
- `nginx/` - Nginx config with SSL/TLS, rate limiting, security headers
- `scripts/` - Deployment, backup, restore, and SQLite-to-PostgreSQL migration scripts
- `monitoring/` - Service health check script

### Backup System

- **Backend**: `BackupService` uses `pg_dump`/`pg_restore` with Bunny CDN offsite storage
- **API**: `/backups/` CRUD endpoints (admin only)
- **Frontend**: Settings > Database Backups page
- **Scripts**: `scripts/backup.sh` (scheduled), `scripts/restore.sh` (CLI)
- CDN path: `spondadmin/backups/` in the shared `archery-trainer-storage` Bunny CDN zone

### Migration Management

- **Backend**: `MigrationService` wraps Alembic operations (status, history, run)
- **API**: `/migrations/status`, `/migrations/history`, `/migrations/run` (admin only)
- **Frontend**: Settings > Migrations page

## Configuration

### Docker Development
Uses `backend/.env.docker` with PostgreSQL defaults. Just run `docker compose up`.

### Local Development
Backend config via `backend/.env` (copy from `.env.example`):
- `SPOND_USERNAME` / `SPOND_PASSWORD` - Spond API credentials
- `SECRET_KEY` - JWT signing key (generate with `openssl rand -hex 32`)
- `AUTO_SYNC_ENABLED` - Enable background sync
- `SYNC_*_INTERVAL_MINUTES` - Sync frequency per entity

### Production
Copy `.env.production.example` to `.env` and configure:
- `DATABASE_URL` - PostgreSQL connection (asyncpg)
- `POSTGRES_PASSWORD` - Strong database password
- `SECRET_KEY` - JWT signing key
- `BUNNY_STORAGE_ZONE`, `BUNNY_STORAGE_API_KEY`, `BUNNY_CDN_HOSTNAME` - CDN backup storage
- `ALLOWED_ORIGINS` - JSON array format: `["https://admin.lillehammerbueskyttere.no"]`

Frontend config via `frontend/.env`:
- `NUXT_PUBLIC_API_BASE` - Backend API URL (default: `http://localhost:8001/api/v1`)

## API Endpoints

Base URL: `http://localhost:8001/api/v1`

- `/auth/login` - JWT authentication
- `/events/`, `/events/sync`, `/events/{id}` - Event management
- `/groups/`, `/groups/sync`, `/groups/{id}` - Group management
- `/members/`, `/members/sync`, `/members/{id}` - Member management
- `/analytics/summary`, `/analytics/attendance-trends`, `/analytics/response-rates` - Analytics
- `/analytics/organizers` - Organizer statistics with attendance tracking
- `/analytics/categories/*` - Category-specific analytics
- `/reports/`, `/reports/{id}`, `/reports/{id}/generate` - Report management
- `/scheduler/status`, `/scheduler/jobs` - Background job management
- `/scores/results`, `/scores/competitions`, `/scores/records`, `/scores/statistics` - Competition scores
- `/scraper/run`, `/scraper/status`, `/scraper/config` - bueskyting.no scraper
- `/backups/`, `/backups/{id}/restore`, `/backups/{id}/upload-cdn` - Database backups
- `/migrations/status`, `/migrations/history`, `/migrations/run` - Migration management
- `/docs` - Swagger UI

## Important Patterns

**Timestamp Handling**: SQLAlchemy models use `TimestampMixin`. When creating records via sync services, explicitly set `created_at` and `updated_at` fields. Use timezone-naive datetimes with PostgreSQL (`TIMESTAMP WITHOUT TIME ZONE`).

**bcrypt Compatibility**: Pin `bcrypt==4.0.1` in requirements.txt. Newer bcrypt versions break `passlib` on Python 3.13.

**Analytics Response Format**: Event responses are stored as JSON with structure `{"responses": [...], "accepted_uids": [...]}`. The `analytics_service.py` uses `_get_responses_array()` helper for backward compatibility.

**Nuxt UI CSS**: The `assets/css/main.css` must contain both `@import "tailwindcss"` and `@import "@nuxt/ui"` for proper styling.

**NuxtPage Key**: `app.vue` uses `<NuxtPage :key="$route.fullPath" />` to force re-renders on route changes.

**Nuxt UI v3 Multiple Selection**: When using `USelectMenu` with `multiple` prop, DO NOT use `value-attribute`. Instead, work with full objects:
```vue
<!-- ❌ Wrong -->
<USelectMenu v-model="selected" :items="options" multiple value-attribute="value" />

<!-- ✅ Correct -->
<USelectMenu v-model="selected" :items="options" multiple />
<!-- where selected is ref<{label: string, value: any}[]> -->
```

**Organizer Tracking**: Event organizers are extracted from `event.raw_data.owners` field. The `get_events_with_attendance()` service method includes organizer information with their response status (accepted/declined/unanswered).

**ALLOWED_ORIGINS Format**: Must be a JSON array in `.env` files: `ALLOWED_ORIGINS=["http://localhost:3000"]`. Comma-separated strings will fail pydantic validation.

**Role-Based Access**: Three roles: `admin` (full access), `editor` (modify data), `viewer` (read-only). Use `get_current_admin`, `get_current_editor_or_above` dependencies from `app/core/deps.py`. The `usePermissions` composable provides frontend guards.

## Reporting System

The application includes a comprehensive reporting system with detailed statistics tables:

### Report Types
- **Category Breakdown** - Event distribution by category
- **Attendance Trends** - Attendance patterns over time
- **Comprehensive** - All metrics with detailed tables

### Available Metrics (Comprehensive Reports)
- `summary` - Overall statistics summary
- `category_distribution` - Event count by category with charts
- `attendance_trends` - Time-series attendance data with period selection
- `response_rates` - Accept/decline/unanswered statistics
- `member_participation` - Detailed member attendance with sortable table
- `event_details` - Event list with responses and organizer tracking
- `category_details` - Per-category statistics with attendance rates
- `attendance_log` - Daily attendance breakdown
- `organizer_statistics` - Organizer activity and their own attendance rates

### Detailed Statistics Tables

All report tables in `components/reports/` include:
- **Sortable columns** - Click any header to sort ascending/descending
- **Filtering** - Search by name, filter by category, date range, or thresholds
- **Calculations footer** - Dynamic totals and averages that update with filters
- **Pagination** - Configurable page size (10/20/50/100 items per page)
- **Color coding** - Green (accepted), red (declined), gray (unanswered/no response)

Tables use the `useTableState` composable for consistent sorting and pagination behavior.

### Report Generation Flow
1. User creates report via `/dashboard/reports/new` with configuration (date range, categories, metrics)
2. Backend `ReportService.generate_report()` fetches data from analytics service
3. Frontend displays charts (Chart.js) and detailed tables (custom Vue components)
4. Users can export reports to CSV format

### Organizer Features
- Organizers are tracked for each event with their attendance status
- Analytics dashboard shows top 10 most active organizers
- Reports include organizer columns showing who organized events and their responses
- Organizer statistics show events organized vs their own attendance rates

## Competition Scores System

### Architecture
- **Scraper**: `bueskyting_scraper_service.py` scrapes competition results and records from bueskyting.no using crawl4ai
- **Models**: `Competition`, `CompetitionResult`, `ArcherStatistics`, `ArcheryRecord`, `ArcherProfile`
- **Matching**: `archer_matching_service.py` links bueskyting.no archers to Spond members using fuzzy name matching (rapidfuzz)
- **Frontend**: `/dashboard/scores/` pages for results, competitions, records, and statistics

### Archer Profiles
- Link Spond members to bueskyting.no profiles via `bueskyting_id`
- Store bow type, age class, and other archery-specific data
- `ArcherProfileForm.vue` component for editing profiles on member detail pages

### Scraper Configuration
- Managed via Settings > Competition Scraper
- Configurable base URLs, club ID, auto-scrape interval
- Unmatched archer management with auto-match and manual match options

## Deployment

### Production Domain
`admin.lillehammerbueskyttere.no`

### First-Time Setup
1. Copy `.env.production.example` to `.env`, fill in all values
2. Set up SSL: `certbot certonly --webroot -w /var/www/certbot -d admin.lillehammerbueskyttere.no`
3. Run `./scripts/deploy.sh`
4. Create admin user: `docker compose -f docker-compose.prod.yml exec backend python3 create_admin.py`

### SQLite to PostgreSQL Migration
For migrating existing data from local SQLite to Docker PostgreSQL:
```bash
docker compose up db -d
docker compose exec backend alembic upgrade head
python3 scripts/migrate-sqlite-to-postgres.py
```
