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

### Planned
- 📋 Background synchronization with scheduled tasks
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

8. **Phase 8: Background Synchronization** 📋 Planned
   - Scheduled automatic sync
   - Webhook support for real-time updates
   - Background task management

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
