#!/usr/bin/env python3
"""
Quick verification script - checks code structure without running the server
Can run without virtual environment
"""

import sys
import os
from pathlib import Path

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
BOLD = '\033[1m'
NC = '\033[0m'

def print_status(message, status):
    """Print status message"""
    symbol = f"{GREEN}✓{NC}" if status else f"{RED}✗{NC}"
    print(f"{symbol} {message}")

def check_file(path, description):
    """Check if file exists"""
    exists = Path(path).exists()
    print_status(f"{description}: {path}", exists)
    return exists

def check_directory(path, description):
    """Check if directory exists"""
    exists = Path(path).is_dir()
    print_status(f"{description}: {path}", exists)
    return exists

def main():
    """Main verification"""
    print(f"{BOLD}{'='*50}")
    print("Spond Admin API - Code Structure Verification")
    print(f"{'='*50}{NC}\n")

    all_pass = True

    # Check Python version
    print(f"{BLUE}Python Environment:{NC}")
    version = sys.version.split()[0]
    major, minor = map(int, version.split('.')[:2])
    py_ok = major == 3 and minor >= 10
    print_status(f"Python version {version} (requires 3.10+)", py_ok)
    all_pass = all_pass and py_ok
    print()

    # Check project structure
    print(f"{BLUE}Project Structure:{NC}")
    dirs = [
        ("app", "Main application directory"),
        ("app/models", "Database models"),
        ("app/services", "Business logic services"),
        ("app/api/v1", "API endpoints"),
        ("app/core", "Core utilities"),
        ("app/schemas", "Pydantic schemas"),
        ("alembic", "Database migrations"),
    ]
    for dir_path, desc in dirs:
        result = check_directory(dir_path, desc)
        all_pass = all_pass and result
    print()

    # Check key files
    print(f"{BLUE}Key Files:{NC}")
    files = [
        ("app/main.py", "FastAPI application"),
        ("app/core/config.py", "Configuration"),
        ("app/core/security.py", "Security utilities"),
        ("app/core/deps.py", "Dependencies"),
        ("app/db/session.py", "Database session"),
        ("app/models/admin.py", "Admin model"),
        ("app/models/event.py", "Event model"),
        ("app/services/spond_service.py", "Spond service"),
        ("app/services/admin_service.py", "Admin service"),
        ("app/services/event_service.py", "Event service"),
        ("app/services/event_sync_service.py", "Event sync service"),
        ("app/api/v1/auth.py", "Auth API"),
        ("app/api/v1/events.py", "Events API"),
        ("requirements.txt", "Dependencies"),
        (".env", "Environment config"),
        ("create_admin.py", "Admin creation script"),
    ]
    for file_path, desc in files:
        result = check_file(file_path, desc)
        all_pass = all_pass and result
    print()

    # Check test scripts
    print(f"{BLUE}Test Scripts:{NC}")
    scripts = [
        ("test_auth.sh", "Auth tests"),
        ("test_events.sh", "Events tests"),
        ("run_all_tests.sh", "Complete test suite"),
        ("setup_and_test.sh", "Setup script"),
    ]
    for script_path, desc in scripts:
        result = check_file(script_path, desc)
        all_pass = all_pass and result
    print()

    # Try importing key modules (without running)
    print(f"{BLUE}Code Syntax Check:{NC}")

    sys.path.insert(0, str(Path.cwd()))

    modules_to_check = [
        ("app.core.config", "Configuration module"),
        ("app.core.security", "Security module"),
        ("app.models.admin", "Admin model"),
        ("app.models.event", "Event model"),
        ("app.schemas.admin", "Admin schemas"),
        ("app.schemas.event", "Event schemas"),
    ]

    for module_name, desc in modules_to_check:
        try:
            __import__(module_name)
            print_status(f"{desc} syntax", True)
        except ImportError as e:
            print_status(f"{desc} syntax (missing deps: {e})", False)
        except SyntaxError as e:
            print_status(f"{desc} syntax: {e}", False)
            all_pass = False
        except Exception as e:
            # Other errors are ok (e.g., missing .env), we just check syntax
            print_status(f"{desc} syntax", True)
    print()

    # Summary
    print(f"{BOLD}{'='*50}")
    if all_pass:
        print(f"{GREEN}All structure checks passed!{NC}")
        print(f"\nNext steps:")
        print(f"1. Install python3-venv: {YELLOW}sudo apt install python3.13-venv{NC}")
        print(f"2. Follow INSTALL_INSTRUCTIONS.md")
        print(f"3. Run the test suite")
    else:
        print(f"{RED}Some checks failed!{NC}")
        print(f"\nPlease review the errors above.")
    print(f"{'='*50}{NC}")

if __name__ == "__main__":
    main()
