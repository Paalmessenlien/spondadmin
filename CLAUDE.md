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
- `pages/dashboard/` - Main app pages (events/, groups/, members/, analytics.vue, reports/)
- `components/` - Reusable Vue components (charts, empty states, breadcrumbs)
  - `components/reports/` - Report-specific table components with sorting/filtering
- `composables/` - Composable functions for shared logic
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
- `/analytics/organizers` - Organizer statistics with attendance tracking
- `/analytics/categories/*` - Category-specific analytics
- `/reports/`, `/reports/{id}`, `/reports/{id}/generate` - Report management
- `/scheduler/status`, `/scheduler/jobs` - Background job management
- `/docs` - Swagger UI

## Important Patterns

**Timestamp Handling**: SQLAlchemy models use `TimestampMixin`. When creating records via sync services, explicitly set `created_at` and `updated_at` fields for SQLite compatibility.

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
