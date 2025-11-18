# Spond Admin Frontend

A modern admin interface for managing Spond events, groups, and members built with Nuxt 3 and Nuxt UI.

## Features

- 🔐 **Authentication** - Secure login with JWT tokens
- 📊 **Dashboard** - Overview with statistics and quick actions
- 📅 **Events Management** - View, filter, and sync events from Spond
- 👥 **Groups Management** - Manage groups and subgroups
- 👤 **Members Management** - View and sync member data
- 🎨 **Nuxt UI** - Beautiful, accessible components
- 🌙 **Dark Mode** - Built-in dark mode support
- 📱 **Responsive** - Works on all devices

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
NUXT_PUBLIC_API_BASE=http://localhost:8001/api/v1
```

3. Run development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000` (or 3001 if 3000 is in use).

## Default Credentials

- **Username**: `testadmin`
- **Password**: `testpassword123`

## Project Structure

```
frontend/
├── pages/              # Application pages
│   ├── index.vue       # Home page (redirects)
│   ├── login.vue       # Login page
│   └── dashboard/      # Dashboard pages
│       ├── index.vue   # Dashboard home
│       ├── events.vue  # Events management
│       ├── groups.vue  # Groups management
│       └── members.vue # Members management
├── layouts/            # Application layouts
│   └── dashboard.vue   # Dashboard layout with navigation
├── stores/             # Pinia stores
│   └── auth.ts         # Authentication store
├── composables/        # Composables
│   └── useApi.ts       # API client
└── nuxt.config.ts      # Nuxt configuration
```

## API Integration

The frontend connects to the FastAPI backend running on `http://localhost:8001`.

### Available API Endpoints

- **Authentication**
  - `POST /api/v1/auth/login` - Login
  - `GET /api/v1/auth/me` - Get current user

- **Events**
  - `GET /api/v1/events/` - List events
  - `POST /api/v1/events/sync` - Sync events from Spond
  - `GET /api/v1/events/stats` - Get event statistics
  - `GET /api/v1/events/{id}` - Get single event

- **Groups**
  - `GET /api/v1/groups/` - List groups
  - `POST /api/v1/groups/sync` - Sync groups from Spond
  - `GET /api/v1/groups/stats` - Get group statistics

- **Members**
  - `GET /api/v1/members/` - List members
  - `POST /api/v1/members/sync` - Sync members from Spond
  - `GET /api/v1/members/stats` - Get member statistics

## Technologies

- **Nuxt 3** - Vue.js framework
- **Nuxt UI** - Component library with Tailwind CSS
- **Pinia** - State management
- **TypeScript** - Type safety
- **Zod** - Schema validation
- **Vite** - Fast build tool

## Development

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## License

MIT
