# Group Filtering - Testing Guide

## Overview

Comprehensive Playwright E2E tests have been created to validate the group filtering functionality across all sections of the application.

## Test Files Created

### 1. **Smoke Tests** (`frontend/tests/e2e/group-filtering-smoke.spec.ts`)
Basic tests that verify UI elements and navigation without requiring specific data:
- ✅ Group selector visibility on all pages
- ✅ Page navigation without errors
- ✅ API endpoints respond correctly
- ✅ No JavaScript errors occur

### 2. **Full E2E Tests** (`frontend/tests/e2e/group-filtering.spec.ts`)
Comprehensive tests that validate complete functionality:
- ✅ "All Groups" option display
- ✅ Analytics data filtering by group
- ✅ Events list filtering by group
- ✅ Members list filtering by group
- ✅ Groups hierarchy view
- ✅ LocalStorage persistence across sessions
- ✅ Toast notifications on group selection
- ✅ Pagination reset when group changes
- ✅ Switching between specific group and "All Groups"

## Prerequisites

### 1. Start Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 2. Ensure Test Data Exists
- Admin user: `admin` / `admin`
- At least one synced group
- Some events, members, and analytics data (recommended)

## Running Tests

### Quick Start (All in One)
```bash
./run-e2e-tests.sh
```

### Run smoke tests only (no data required)
```bash
./run-e2e-tests.sh --smoke
```

### Run with UI (interactive mode)
```bash
./run-e2e-tests.sh --ui
```

### Run in headed mode (see browser)
```bash
./run-e2e-tests.sh --headed
```

### Manual Test Execution

#### From frontend directory:
```bash
cd frontend

# All tests
npm run test:e2e

# UI mode
npm run test:e2e:ui

# Headed mode
npm run test:e2e:headed

# Specific test file
npx playwright test group-filtering-smoke.spec.ts

# Single test
npx playwright test -g "should display All Groups option"
```

## Test Configuration

Configuration file: `frontend/playwright.config.ts`

Key settings:
- **Base URL**: `http://localhost:3000`
- **Test directory**: `./tests/e2e`
- **Browser**: Chromium (Desktop Chrome)
- **Timeout**: 120s for server start
- **Retries**: 2 (in CI mode)
- **Screenshot**: On failure only
- **Trace**: On first retry

## Viewing Results

### HTML Report
After running tests:
```bash
cd frontend
npx playwright show-report
```

### Traces
If tests fail, view the trace:
```bash
npx playwright show-trace trace.zip
```

## Test Coverage Matrix

| Feature | Smoke Test | Full E2E Test |
|---------|-----------|--------------|
| Group Selector Display | ✅ | ✅ |
| Page Navigation | ✅ | ✅ |
| Analytics Filtering | ❌ | ✅ |
| Events Filtering | ❌ | ✅ |
| Members Filtering | ❌ | ✅ |
| Groups Hierarchy | ❌ | ✅ |
| LocalStorage Persistence | ❌ | ✅ |
| Toast Notifications | ❌ | ✅ |
| Pagination Reset | ❌ | ✅ |
| API Error Checking | ✅ | ❌ |

## Troubleshooting

### Tests fail to start
**Problem**: Backend not running
**Solution**: Start backend with `python -m uvicorn app.main:app --reload`

### Login fails
**Problem**: Wrong credentials or user doesn't exist
**Solution**: Verify `admin` / `admin` user exists in database

### No groups available
**Problem**: No groups synced
**Solution**: Use "Sync Groups" button in UI or sync via API

### Tests timeout
**Problem**: Slow responses or network issues
**Solution**:
- Check backend is responding quickly
- Increase timeout in `playwright.config.ts`
- Check database performance

### Browser not found
**Problem**: Playwright browsers not installed
**Solution**: `npx playwright install chromium`

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - uses: actions/setup-python@v4

      - name: Install frontend deps
        run: cd frontend && npm ci

      - name: Install Playwright
        run: cd frontend && npx playwright install chromium

      - name: Start backend
        run: cd backend && python -m uvicorn app.main:app &

      - name: Run tests
        run: cd frontend && npm run test:e2e

      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Best Practices

1. **Run smoke tests first** - Quick validation without data dependency
2. **Use UI mode for debugging** - See tests execute in real-time
3. **Check traces on failures** - Detailed execution timeline
4. **Keep test data fresh** - Sync groups regularly
5. **Review HTML reports** - Comprehensive test results

## Continuous Testing

### Watch mode (during development)
```bash
cd frontend
npx playwright test --ui
```

### Quick validation
```bash
./run-e2e-tests.sh --smoke
```

### Full validation before commit
```bash
./run-e2e-tests.sh
```

## Support

For issues or questions:
1. Check test output for specific error messages
2. Review HTML report for detailed results
3. View traces for failed tests
4. Check browser console in headed mode
5. Verify backend logs for API issues
