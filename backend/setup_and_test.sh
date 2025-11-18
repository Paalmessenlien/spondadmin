#!/bin/bash

# Quick setup and test script for Spond Admin API

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}=========================================="
echo "Spond Admin API - Quick Setup"
echo -e "==========================================${NC}"
echo ""

# Step 1: Check Python
echo -e "${BLUE}Step 1: Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
echo ""

# Step 2: Create virtual environment
echo -e "${BLUE}Step 2: Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || {
        echo -e "${YELLOW}Failed to create venv. Install python3-venv:${NC}"
        echo "  sudo apt install python3-venv"
        exit 1
    }
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi
echo ""

# Step 3: Activate and install dependencies
echo -e "${BLUE}Step 3: Installing dependencies...${NC}"
echo "This may take a few minutes..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 4: Check configuration
echo -e "${BLUE}Step 4: Checking configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env to add Spond credentials${NC}"
else
    echo -e "${GREEN}✓ .env exists${NC}"
fi
echo ""

# Step 5: Initialize database
echo -e "${BLUE}Step 5: Initializing database...${NC}"
python3 << 'EOF'
import asyncio
from app.db.session import init_db

async def setup_db():
    await init_db()
    print("Database initialized")

asyncio.run(setup_db())
EOF
echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Step 6: Create admin user
echo -e "${BLUE}Step 6: Creating admin user...${NC}"

# Check if admin exists
ADMIN_EXISTS=$(python3 << 'EOF'
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService

async def check():
    async with AsyncSessionLocal() as db:
        admins = await AdminService.get_all(db)
        return len(admins) > 0

result = asyncio.run(check())
print("yes" if result else "no")
EOF
)

if [ "$ADMIN_EXISTS" = "yes" ]; then
    echo -e "${GREEN}✓ Admin user already exists${NC}"
    echo ""
    python3 << 'EOF'
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService

async def list_admins():
    async with AsyncSessionLocal() as db:
        admins = await AdminService.get_all(db)
        print("Existing admins:")
        for admin in admins:
            print(f"  • {admin.username} ({admin.email})")

asyncio.run(list_admins())
EOF
else
    echo "No admin users found. Let's create one!"
    echo ""
    python3 create_admin.py
fi
echo ""

# Step 7: Done!
echo -e "${BOLD}${GREEN}=========================================="
echo "Setup Complete!"
echo -e "==========================================${NC}"
echo ""
echo "To start the server:"
echo -e "  ${BLUE}source venv/bin/activate${NC}"
echo -e "  ${BLUE}uvicorn app.main:app --reload${NC}"
echo ""
echo "Then in another terminal, run tests:"
echo -e "  ${BLUE}cd /home/paal/spond/backend${NC}"
echo -e "  ${BLUE}source venv/bin/activate${NC}"
echo -e "  ${BLUE}./run_all_tests.sh${NC}"
echo ""
echo "Or visit: ${BLUE}http://localhost:8000/api/v1/docs${NC}"
echo ""
echo -e "${YELLOW}Don't forget to add your Spond credentials to .env!${NC}"
