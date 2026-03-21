"""Test Gitea API endpoints."""
import requests
import os

# Set environment variables for testing
os.environ['GITEA_URL'] = 'http://localhost:8080'
os.environ['GITEA_OWNER'] = 'root'
os.environ['GITEA_REPO'] = 'cheersAI'
os.environ['GITEA_TOKEN'] = 'test_token'

BASE_URL = 'http://localhost:5001/console/api'

print("Testing Gitea API endpoints...")
print("=" * 50)

# Test 1: List files endpoint (without auth - should get 401)
print("\n1. Testing GET /gitea/files (no auth)")
try:
    response = requests.get(f'{BASE_URL}/gitea/files?path=')
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   ✓ Correctly requires authentication")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Config endpoint (without auth - should get 401)
print("\n2. Testing GET /gitea/config (no auth)")
try:
    response = requests.get(f'{BASE_URL}/gitea/config')
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   ✓ Correctly requires authentication")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Check if endpoints are registered
print("\n3. Checking registered endpoints...")
try:
    # Try to access the API documentation
    response = requests.get('http://localhost:5001/')
    print(f"   Backend is running: {response.status_code == 200}")
except Exception as e:
    print(f"   ✗ Backend not accessible: {e}")

print("\n" + "=" * 50)
print("Test complete!")
print("\nNote: 401 errors are expected without authentication.")
print("The important thing is that the endpoints exist and respond.")
