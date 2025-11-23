#!/usr/bin/env python3
"""
Trigger sync from Spond API
"""
import httpx
import sys

BASE_URL = "http://127.0.0.1:8001/api/v1"

def main():
    # Login
    print("Logging in...")
    login_response = httpx.post(
        f"{BASE_URL}/auth/login",
        json={"username": "testadmin", "password": "TestPass123!"}
    )

    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(login_response.text)
        sys.exit(1)

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Sync groups
    print("\n=== Syncing Groups ===")
    groups_response = httpx.post(f"{BASE_URL}/groups/sync", headers=headers)
    print(f"Status: {groups_response.status_code}")
    print(groups_response.json())

    # Sync events
    print("\n=== Syncing Events ===")
    events_response = httpx.post(
        f"{BASE_URL}/events/sync",
        headers=headers,
        params={"max_events": 100}
    )
    print(f"Status: {events_response.status_code}")
    print(events_response.json())

    # Sync members
    print("\n=== Syncing Members ===")
    members_response = httpx.post(f"{BASE_URL}/members/sync", headers=headers)
    print(f"Status: {members_response.status_code}")
    print(members_response.json())

if __name__ == "__main__":
    main()
