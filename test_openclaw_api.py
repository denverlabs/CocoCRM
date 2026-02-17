#!/usr/bin/env python3
"""
Test script for OpenClaw API integration
Tests all authentication methods and API endpoints
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://cococrm.onrender.com"  # Change to your deployment URL
API_KEY = "sk-openclaw-2026-your-secret-key"  # Change to your actual API key

def test_api_key_header():
    """Test authentication with X-API-Key header (recommended)"""
    print("\n🧪 Test 1: X-API-Key Header Authentication")
    print("=" * 60)

    response = requests.get(
        f"{BASE_URL}/api/contacts",
        headers={"X-API-Key": API_KEY},
        params={"username": "admin"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Got {len(data.get('contacts', []))} contacts")
        return True
    else:
        print(f"❌ FAILED: {response.status_code} - {response.text}")
        return False

def test_bearer_auth():
    """Test authentication with Authorization Bearer header"""
    print("\n🧪 Test 2: Bearer Token Authentication")
    print("=" * 60)

    response = requests.get(
        f"{BASE_URL}/api/contacts",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"username": "admin"}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Got {len(data.get('contacts', []))} contacts")
        return True
    else:
        print(f"❌ FAILED: {response.status_code} - {response.text}")
        return False

def test_query_param():
    """Test authentication with query parameter"""
    print("\n🧪 Test 3: Query Parameter Authentication")
    print("=" * 60)

    response = requests.get(
        f"{BASE_URL}/api/contacts",
        params={"username": "admin", "api_key": API_KEY}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS: Got {len(data.get('contacts', []))} contacts")
        return True
    else:
        print(f"❌ FAILED: {response.status_code} - {response.text}")
        return False

def test_create_contact():
    """Test creating a contact via API"""
    print("\n🧪 Test 4: Create Contact")
    print("=" * 60)

    contact_data = {
        "username": "admin",
        "name": "Test Contact",
        "email": f"test{int(requests.get('https://httpbin.org/uuid').json()['uuid'].split('-')[0], 16)}@test.com",
        "company": "OpenClaw AI",
        "position": "AI Agent",
        "phone": "+1234567890",
        "tags": "test,api,openclaw"
    }

    response = requests.post(
        f"{BASE_URL}/api/contacts",
        headers={"X-API-Key": API_KEY},
        json=contact_data
    )

    if response.status_code == 201:
        data = response.json()
        print(f"✅ SUCCESS: Created contact ID {data['contact']['id']}")
        print(f"   Name: {data['contact']['name']}")
        print(f"   Email: {data['contact']['email']}")
        return True
    else:
        print(f"❌ FAILED: {response.status_code} - {response.text}")
        return False

def test_create_task():
    """Test creating a task via API"""
    print("\n🧪 Test 5: Create Task")
    print("=" * 60)

    task_data = {
        "username": "admin",
        "title": "Test API Integration",
        "description": "Testing OpenClaw API endpoint",
        "priority": "high",
        "due_date": "2026-03-01T10:00:00"
    }

    response = requests.post(
        f"{BASE_URL}/api/tasks",
        headers={"X-API-Key": API_KEY},
        json=task_data
    )

    if response.status_code == 201:
        data = response.json()
        print(f"✅ SUCCESS: Created task ID {data['task']['id']}")
        print(f"   Title: {data['task']['title']}")
        print(f"   Priority: {data['task']['priority']}")
        return True
    else:
        print(f"❌ FAILED: {response.status_code} - {response.text}")
        return False

def test_invalid_key():
    """Test that invalid API key is rejected"""
    print("\n🧪 Test 6: Invalid API Key (should fail)")
    print("=" * 60)

    response = requests.get(
        f"{BASE_URL}/api/contacts",
        headers={"X-API-Key": "invalid-key-123"},
        params={"username": "admin"}
    )

    if response.status_code == 401:
        print("✅ SUCCESS: Invalid key correctly rejected")
        return True
    else:
        print(f"❌ FAILED: Expected 401, got {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🤖 OpenClaw CRM API Integration Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:20]}...")
    print("="*60)

    tests = [
        test_api_key_header,
        test_bearer_auth,
        test_query_param,
        test_create_contact,
        test_create_task,
        test_invalid_key
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.append(False)

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! OpenClaw API is ready to use!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check configuration and try again.")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    if len(sys.argv) > 2:
        API_KEY = sys.argv[2]

    sys.exit(main())
