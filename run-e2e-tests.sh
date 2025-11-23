#!/bin/bash
# Script to run E2E tests for group filtering functionality

set -e

echo "🧪 Group Filtering E2E Test Runner"
echo "=================================="
echo ""

# Check if backend is running
echo "📡 Checking backend server..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend server is running on http://localhost:8000"
else
    echo "❌ Backend server is NOT running"
    echo ""
    echo "Please start the backend server first:"
    echo "  cd backend"
    echo "  python -m uvicorn app.main:app --reload"
    echo ""
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo ""
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if Playwright browsers are installed
if [ ! -d "$HOME/.cache/ms-playwright/chromium-1194" ]; then
    echo ""
    echo "🌐 Installing Playwright browsers..."
    npx playwright install chromium
fi

echo ""
echo "🚀 Starting tests..."
echo ""

# Run the tests
if [ "$1" == "--ui" ]; then
    echo "Running tests in UI mode..."
    npm run test:e2e:ui
elif [ "$1" == "--headed" ]; then
    echo "Running tests in headed mode..."
    npm run test:e2e:headed
elif [ "$1" == "--smoke" ]; then
    echo "Running smoke tests only..."
    npx playwright test group-filtering-smoke.spec.ts
else
    echo "Running all tests..."
    npm run test:e2e
fi

echo ""
echo "✅ Tests complete!"
echo ""
echo "To view the HTML report:"
echo "  npx playwright show-report"
