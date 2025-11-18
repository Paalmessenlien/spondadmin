# Spond Admin Interface

A full-stack web application for managing Spond events, groups, and members.

## Quick Start

```bash
# 1. Start the backend
cd backend
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

# 2. Start the frontend (in a new terminal)
cd frontend
npm run dev

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/api/v1/docs

# 4. Login with default credentials
# Username: testadmin
# Password: testpass
```

## Overview

This project provides an administrative interface for [Spond](https://spond.com), a team and group-oriented events management system. It allows administrators to:

- View and manage events (practices, games, meetings)
- Track attendance and member responses
- Manage groups, members, roles, and subgroups
- View detailed event pages with attendee lists
- Access member profiles with participation history
- Explore group details with member rosters
- Analyze attendance trends and response rates with interactive charts
- View participation statistics and member leaderboards

## Architecture

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy (async)
- **API Integration**: `spond` and `spond-classes` libraries
- **Authentication**: JWT tokens with bcrypt password hashing

### Frontend
- **Framework**: Nuxt 3 (Vue.js)
- **UI Library**: Nuxt UI v3 (with Tailwind CSS v4)
- **State Management**: Pinia
- **API Client**: Fetch API ($fetch)
- **Charts**: Chart.js with vue-chartjs
- **Validation**: Zod schema validation
- **Icons**: Nuxt Icon with @iconify-json/heroicons and @iconify-json/lucide

**Note**: The frontend uses Nuxt UI v3 which requires both `@import "tailwindcss"` and `@import "@nuxt/ui"` in the main CSS file for proper styling.

## Project Structure

```
spond/
├── backend/           # FastAPI backend application
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # Config and security
│   │   ├── db/        # Database setup
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # Business logic
│   ├── alembic/       # Database migrations
│   └── requirements.txt
├── frontend/          # Nuxt 3 frontend (to be created)
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Spond account credentials

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Spond credentials and settings
   ```

4. Run the backend:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
   ```

   API will be available at http://localhost:8001
   API docs at http://localhost:8001/api/v1/docs

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

   Frontend will be available at http://localhost:3000

### Default Login Credentials

**Username**: `testadmin`
**Password**: `testpass`

⚠️ **Important**: Change these credentials in production!

## Features

### Completed

**Phase 1: Backend Foundation** ✅
- ✅ Backend project structure
- ✅ Database models and migrations
- ✅ Spond API service wrapper
- ✅ Configuration management
- ✅ Security utilities (JWT, password hashing)

**Phase 2: Authentication System** ✅
- ✅ Admin user management
- ✅ JWT authentication
- ✅ Login/logout API endpoints
- ✅ Role-based access control

**Phase 3: Events API** ✅
- ✅ Sync events from Spond API
- ✅ List/filter/search events
- ✅ Event statistics
- ✅ Update events
- ✅ Export attendance (Excel)
- ✅ Manage event responses

**Phase 4: Groups & Members API** ✅
- ✅ Group synchronization from Spond
- ✅ Member synchronization from Spond
- ✅ List and filter groups/members
- ✅ Group and member statistics
- ✅ Update groups and members

**Phase 5: Frontend Application** ✅
- ✅ Nuxt 3 project setup with Nuxt UI
- ✅ Authentication pages (login)
- ✅ Dashboard layout and navigation
- ✅ Events management UI
- ✅ Groups management UI
- ✅ Members management UI
- ✅ Real-time statistics dashboard
- ✅ Sync functionality for all data

**Phase 6: Analytics & Advanced Features** ✅
- ✅ Analytics backend service with comprehensive queries
- ✅ Analytics API endpoints (`/api/v1/analytics/*`)
- ✅ Chart.js and vue-chartjs integration
- ✅ Attendance trends chart (line chart with weekly/monthly/yearly views)
- ✅ Response rate distribution chart (doughnut chart)
- ✅ Event type distribution chart (bar chart)
- ✅ Member participation tracking and leaderboard
- ✅ Analytics summary dashboard

**Phase 7: Detail Pages & Enhanced Views** ✅
- ✅ Event detail page with attendee list and tabbed view
- ✅ Member profile page with participation history
- ✅ Group detail page with member roster and subgroups
- ✅ Navigation links from list pages to detail pages
- ✅ Search functionality on detail pages
- ✅ Statistics cards on all detail pages

**Phase 8: Background Synchronization** ✅
- ✅ Background scheduler service with APScheduler
- ✅ Scheduled automatic sync for events, groups, and members
- ✅ Configurable sync intervals via environment variables
- ✅ API endpoints for job management and monitoring
- ✅ Graceful scheduler lifecycle management (startup/shutdown)

### Planned
- 📋 Advanced filtering and multi-select options
- 📋 Export reports to PDF/Excel
- 📋 Docker deployment and production setup

## Development Roadmap

1. **Phase 1: Backend Foundation** ✅ Complete
   - FastAPI project structure
   - SQLAlchemy async models
   - Alembic migrations
   - Configuration management
   - Security utilities

2. **Phase 2: Authentication System** ✅ Complete
   - Admin user CRUD operations
   - JWT token-based authentication
   - Login/logout endpoints
   - Role-based access control
   - Password hashing with bcrypt

3. **Phase 3: Events API** ✅ Complete
   - Sync from Spond API
   - List and filter events
   - Event statistics
   - Individual event details
   - Update events

4. **Phase 4: Groups & Members API** ✅ Complete
   - Group synchronization from Spond
   - Member synchronization from Spond
   - List and filter groups/members
   - Group and member statistics
   - Full CRUD operations

5. **Phase 5: Frontend Application** ✅ Complete
   - Nuxt 3 project with Nuxt UI
   - Complete authentication flow
   - Dashboard with real-time statistics
   - Events, Groups, Members management pages
   - Responsive design with dark mode

6. **Phase 6: Analytics & Advanced Features** ✅ Complete
   - Analytics backend service
   - Analytics API endpoints
   - Chart.js and vue-chartjs integration
   - Attendance trends, response rates, event type distribution
   - Member participation leaderboard

7. **Phase 7: Detail Pages & Enhanced Views** ✅ Complete
   - Event detail page with attendee list
   - Member profile page with participation history
   - Group detail page with member roster
   - Navigation links and search functionality

8. **Phase 8: Background Synchronization** ✅ Complete
   - Background scheduler service with APScheduler
   - Scheduled automatic sync for events, groups, and members
   - Configurable sync intervals via environment variables
   - API endpoints for job management and monitoring

9. **Phase 9: Production Deployment** 📋 Planned
   - Docker containers
   - PostgreSQL for production database
   - Environment-based configuration
   - CI/CD pipeline

## API Documentation

The backend provides automatic API documentation:

- **Swagger UI**: http://localhost:8001/api/v1/docs
- **ReDoc**: http://localhost:8001/api/v1/redoc

### Main API Endpoints

**Authentication:**
- `POST /api/v1/auth/login` - Login with username/password
- `GET /api/v1/auth/me` - Get current user info

**Events:**
- `GET /api/v1/events/` - List events (with filters)
- `POST /api/v1/events/sync` - Sync from Spond
- `GET /api/v1/events/stats` - Get statistics
- `GET /api/v1/events/{id}` - Get single event
- `PUT /api/v1/events/{id}` - Update event

**Groups:**
- `GET /api/v1/groups/` - List groups (with filters)
- `POST /api/v1/groups/sync` - Sync from Spond
- `GET /api/v1/groups/stats` - Get statistics
- `GET /api/v1/groups/{id}` - Get single group
- `PUT /api/v1/groups/{id}` - Update group

**Members:**
- `GET /api/v1/members/` - List members (with filters)
- `POST /api/v1/members/sync` - Sync from Spond
- `GET /api/v1/members/stats` - Get statistics
- `GET /api/v1/members/{id}` - Get single member
- `PUT /api/v1/members/{id}` - Update member

**Analytics:**
- `GET /api/v1/analytics/summary` - Overall analytics summary
- `GET /api/v1/analytics/attendance-trends` - Attendance trends over time (supports period: week/month/year)
- `GET /api/v1/analytics/response-rates` - Response rate statistics
- `GET /api/v1/analytics/event-types` - Event type distribution
- `GET /api/v1/analytics/member-participation` - Top members by participation

**Scheduler:**
- `GET /api/v1/scheduler/status` - Get scheduler status and job list
- `GET /api/v1/scheduler/jobs` - List all scheduled background jobs
- `POST /api/v1/scheduler/jobs/{job_id}/trigger` - Manually trigger a scheduled job

## Frontend Pages

**Main Pages:**
- `/login` - Authentication page
- `/dashboard` - Main dashboard with statistics and quick actions
- `/dashboard/analytics` - Analytics dashboard with charts and insights

**List Pages:**
- `/dashboard/events` - Events list with filters and search
- `/dashboard/groups` - Groups list with subgroup information
- `/dashboard/members` - Members list with pagination

**Detail Pages:**
- `/dashboard/events/{id}` - Event detail with attendee list and statistics
- `/dashboard/members/{id}` - Member profile with participation history
- `/dashboard/groups/{id}` - Group detail with member roster and subgroups

## Database Schema

### Tables
- `admins` - Admin users with authentication
- `events` - Cached Spond events with responses
- `groups` - Spond groups with roles and subgroups
- `members` - Group members with profiles
- `sync_history` - API synchronization tracking
- `audit_logs` - Admin action logging

## Security

- Admin passwords hashed with bcrypt
- JWT tokens for API authentication
- Spond credentials stored in environment variables
- All sensitive data in `.env` (not committed to git)

## Recent Updates

### Navigation and Routing Fixes (2025-01-18) ✅

**Problem**: Event, group, and member detail pages were not loading when clicking on items. The URL would change (e.g., to `/dashboard/events/1`) but the page content wouldn't update, showing the list page instead.

**Root Cause**: Nuxt 3 routing conflict - having both a file (`page.vue`) and a directory (`page/`) with the same name causes the file to take precedence over the directory, making nested dynamic routes (`[id].vue`) inaccessible.

**Solutions Applied**:

1. **Fixed Route Structure** (3 pages affected):
   - Moved `pages/dashboard/events.vue` → `pages/dashboard/events/index.vue`
   - Moved `pages/dashboard/groups.vue` → `pages/dashboard/groups/index.vue`
   - Moved `pages/dashboard/members.vue` → `pages/dashboard/members/index.vue`

2. **Added NuxtPage Key** (`frontend/app.vue:5`):
   ```vue
   <NuxtPage :key="$route.fullPath" />
   ```
   This forces page re-rendering when navigating between dynamic routes with the same component.

3. **Fixed Mobile Menu Visibility** (`frontend/layouts/dashboard.vue:117,196`):
   ```vue
   <USlideover v-model="mobileMenuOpen" side="left" class="md:hidden">
   <USlideover v-model="userMenuOpen" side="right" class="md:hidden">
   ```
   Added responsive Tailwind classes to hide mobile navigation menus on desktop screens (≥768px).

**Results**:
- ✅ All navigation working correctly
- ✅ Event detail pages load with full information (breadcrumbs, event data, attendee lists, statistics)
- ✅ Group detail pages show complete data (members, subgroups, roles)
- ✅ Member detail pages accessible
- ✅ Breadcrumb navigation functional (back/forward between list and detail pages)
- ✅ Mobile menus properly hidden on desktop
- ✅ Responsive design maintained across all screen sizes

**Testing**: Verified with Playwright MCP automated browser testing to ensure all navigation flows work correctly.

### Spond Sync Fixes (2025-11-18) ✅

**Problem**: Spond event synchronization was failing with database constraint errors and only syncing a limited number of events (96 instead of 481+). The sync would fail when trying to create new events with error: `NOT NULL constraint failed: events.created_at`.

**Root Causes**:

1. **Database Timestamp Issue**: The `TimestampMixin` uses `server_default=func.now()` which works well with PostgreSQL but has limitations with SQLite. When creating new records, the sync services weren't explicitly setting `created_at` and `updated_at` values, causing constraint violations.

2. **Max Events Limit Too Low**: The default `max_events` parameter was set to only 100 events, artificially limiting sync capacity.

**Solutions Applied**:

1. **Fixed Timestamp Handling** (3 sync services affected):
   - `backend/app/services/event_sync_service.py:168-191`: Added explicit `created_at` and `updated_at` timestamps for new events and `updated_at` for updates
   - `backend/app/services/group_sync_service.py:125-151`: Added explicit timestamp handling for group sync
   - `backend/app/services/member_sync_service.py:182-213`: Added explicit timestamp handling for member sync

   ```python
   # Example fix pattern
   now = datetime.utcnow()
   new_event = Event(
       spond_id=spond_id,
       # ... other fields ...
       created_at=now,
       updated_at=now,
   )
   ```

2. **Increased Event Limit** (`backend/app/api/v1/events.py:31`):
   - Changed default `max_events` from 100 → 500
   - Allows syncing more events per operation

**Results**:
- ✅ **500 events** successfully fetched and synced from Spond API
- ✅ **481 total events** now available in the database (400 created, 100 updated)
- ✅ **0 errors** during sync operation
- ✅ Sync works correctly from both frontend UI and direct API calls
- ✅ All event types synced: EVENT, RECURRING, AVAILABILITY
- ✅ Full date range from 2027 events down to historical data

**Testing**:
- Backend tested with direct API calls using Python requests
- Frontend tested with Playwright MCP automated browser testing
- Verified sync successfully creates new events and updates existing ones
- Screenshot saved at `.playwright-mcp/sync-fixed-481-events.png`

### Phase 8: Background Synchronization (2025-11-18) ✅

**Implementation**: Automated background synchronization system for keeping Spond data up-to-date without manual intervention. The system uses APScheduler to run periodic sync jobs for events, groups, and members at configurable intervals.

**What Was Built**:

1. **Scheduler Service** (`backend/app/services/scheduler_service.py`):
   - AsyncIOScheduler for non-blocking background task execution
   - Three independent sync jobs (events, groups, members)
   - Job management methods (get_jobs, trigger_job)
   - Graceful startup and shutdown handling
   - Error handling and logging for each sync operation

2. **Scheduler API Endpoints** (`backend/app/api/v1/scheduler.py`):
   - `GET /api/v1/scheduler/status` - View scheduler status and active jobs
   - `GET /api/v1/scheduler/jobs` - List all scheduled jobs with next run times
   - `POST /api/v1/scheduler/jobs/{job_id}/trigger` - Manually trigger a specific job

3. **Configuration System** (`backend/app/core/config.py`):
   - `AUTO_SYNC_ENABLED` - Master switch to enable/disable scheduler
   - `SYNC_EVENTS_ENABLED` - Enable/disable event sync job
   - `SYNC_EVENTS_INTERVAL_MINUTES` - Event sync frequency (default: 60 minutes)
   - `SYNC_EVENTS_MAX_EVENTS` - Max events per sync (default: 500)
   - `SYNC_GROUPS_ENABLED` - Enable/disable group sync job
   - `SYNC_GROUPS_INTERVAL_MINUTES` - Group sync frequency (default: 360 minutes)
   - `SYNC_MEMBERS_ENABLED` - Enable/disable member sync job
   - `SYNC_MEMBERS_INTERVAL_MINUTES` - Member sync frequency (default: 360 minutes)

4. **Application Lifecycle Integration** (`backend/app/main.py:28-64`):
   - Scheduler starts automatically during application startup
   - Jobs are scheduled based on configuration
   - Scheduler stops gracefully during shutdown
   - Error handling ensures app starts even if scheduler fails

**How It Works**:

The scheduler service runs in the background and executes sync jobs at specified intervals:

- **Events**: Syncs every 60 minutes (1 hour) by default
- **Groups**: Syncs every 360 minutes (6 hours) by default
- **Members**: Syncs every 360 minutes (6 hours) by default

Each job:
1. Creates a new database session
2. Calls the appropriate sync service (EventSyncService, GroupSyncService, MemberSyncService)
3. Commits the transaction on success
4. Logs results and errors
5. Releases the database session

**Configuration**:

Add these settings to your `.env` file:

```bash
# Enable background synchronization
AUTO_SYNC_ENABLED=true

# Event sync settings
SYNC_EVENTS_ENABLED=true
SYNC_EVENTS_INTERVAL_MINUTES=60
SYNC_EVENTS_MAX_EVENTS=500

# Group sync settings
SYNC_GROUPS_ENABLED=true
SYNC_GROUPS_INTERVAL_MINUTES=360

# Member sync settings
SYNC_MEMBERS_ENABLED=true
SYNC_MEMBERS_INTERVAL_MINUTES=360
```

**Using the API**:

Check scheduler status:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8001/api/v1/scheduler/status
```

List all scheduled jobs:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8001/api/v1/scheduler/jobs
```

Manually trigger a job:
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8001/api/v1/scheduler/jobs/sync_events/trigger
```

**Results**:
- ✅ **3 scheduled jobs** running successfully (sync_events, sync_groups, sync_members)
- ✅ **Automated synchronization** keeps data fresh without manual intervention
- ✅ **Configurable intervals** allow customization for different environments
- ✅ **API management** enables monitoring and manual triggering of sync jobs
- ✅ **Graceful lifecycle** ensures clean startup and shutdown
- ✅ **Error isolation** allows app to run even if individual sync jobs fail

**Testing**:
- Verified scheduler starts successfully with application
- Confirmed all 3 jobs are registered and scheduled
- Tested API endpoints for status, job listing, and manual triggering
- Logs show proper scheduling: "Next wakeup is due at 2025-11-18 13:10:58+01:00"

**Dependencies Added**:
- `APScheduler==3.10.4` - Production-ready job scheduling library

## Troubleshooting

### Frontend CSS Not Loading

If Tailwind CSS or Nuxt UI components are not styled properly, ensure that your `assets/css/main.css` file contains both imports:

```css
@import "tailwindcss";
@import "@nuxt/ui";
```

The `@import "@nuxt/ui";` line is required for Nuxt UI v3 to work properly with Tailwind CSS v4.

### Port Already in Use

If you get a "port already in use" error:

```bash
# Kill processes on port 8001 (backend)
lsof -ti:8001 | xargs kill -9

# Kill processes on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### Database Issues

If you need to reset the database:

```bash
cd backend
rm spond_admin.db  # Delete the SQLite database
alembic upgrade head  # Recreate with migrations
```

Then recreate the admin user or update the password using the admin management endpoints.

## Contributing

This is a private project. For questions or suggestions, please contact the maintainer.

## License

This project uses the unofficial `spond` and `spond-classes` Python libraries, which are licensed under GPL-3.0.

## Acknowledgments

- [spond](https://github.com/Olen/Spond) - Python library for Spond API
- [spond-classes](https://github.com/elliot-100/Spond-classes) - Typed class wrappers for Spond API
- FastAPI, SQLAlchemy, Nuxt, and all other open-source dependencies
