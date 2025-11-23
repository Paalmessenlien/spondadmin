# E2E Tests for Group Filtering

This directory contains Playwright end-to-end tests for the group filtering functionality.

## Prerequisites

Before running the tests, ensure the following:

1. **Backend server is running** on `http://localhost:8000`
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Database is populated with test data**:
   - At least one admin user (default: username=`admin`, password=`admin`)
   - At least one group synced from Spond
   - Some events, members, and analytics data (optional but recommended)

3. **Frontend dependencies are installed**:
   ```bash
   cd frontend
   npm install
   ```

4. **Playwright browsers are installed**:
   ```bash
   npx playwright install chromium
   ```

## Running the Tests

### Run all tests (headless mode):
```bash
npm run test:e2e
```

### Run tests with UI (interactive mode):
```bash
npm run test:e2e:ui
```

### Run tests in headed mode (see browser):
```bash
npm run test:e2e:headed
```

### Run specific test file:
```bash
npx playwright test group-filtering.spec.ts
```

### Run single test:
```bash
npx playwright test group-filtering.spec.ts -g "should display All Groups option"
```

## Test Coverage

The test suite covers:

1. **Group Selector Display**: Verifies "All Groups" option is visible
2. **Analytics Filtering**: Tests data filtering on analytics page
3. **Events Filtering**: Tests event list filtering by group
4. **Members Filtering**: Tests member list filtering by group
5. **Groups Hierarchy**: Tests hierarchy view on groups page
6. **LocalStorage Persistence**: Verifies group selection persists across sessions
7. **Toast Notifications**: Checks success messages on group selection
8. **Pagination Reset**: Ensures pagination resets when group changes
9. **All Groups Selection**: Tests switching back to "All Groups"

## Troubleshooting

### Tests fail immediately
- Ensure backend server is running
- Ensure frontend dev server will be started by Playwright (configured in playwright.config.ts)
- Check that admin user exists in database

### Login fails
- Verify credentials in the test match your database
- Default credentials: `admin` / `admin`

### No groups available
- Sync at least one group from Spond using the "Sync Groups" button
- Or create test data in the database directly

### Tests time out
- Increase timeout in playwright.config.ts
- Check network connectivity
- Ensure backend is responding quickly

## Viewing Test Results

After running tests, view the HTML report:
```bash
npx playwright show-report
```

## Debugging Tests

### Run in debug mode:
```bash
npx playwright test --debug
```

### Generate trace:
```bash
npx playwright test --trace on
```

### View trace:
```bash
npx playwright show-trace trace.zip
```
