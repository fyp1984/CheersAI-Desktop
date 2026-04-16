#!/usr/bin/env python3
"""
Quick diagnostic script to check authentication and workspace status
"""
import requests
import sys

BASE_URL = "http://localhost:5001"

def check_endpoint(endpoint, description):
    """Check if an endpoint is accessible"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✓ Success!")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response (text): {response.text[:200]}")
        else:
            print(f"✗ Failed!")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection Error - Backend not running on port 5001")
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    print("="*60)
    print("Authentication & Workspace Diagnostic Tool")
    print("="*60)
    
    # Check if backend is running
    check_endpoint("/health", "Health Check")
    
    # Check the problematic endpoints
    check_endpoint(
        "/console/api/workspaces/current/model-providers",
        "Model Providers (requires auth)"
    )
    
    check_endpoint(
        "/console/api/workspaces/current/models/model-types/llm",
        "LLM Models (requires auth)"
    )
    
    print("\n" + "="*60)
    print("DIAGNOSIS:")
    print("="*60)
    print("""
If you see 400/401/403 errors above, the issue is authentication.

Solutions:
1. Make sure you're logged in through the web interface
2. Check browser console for authentication errors
3. Verify SSO configuration is correct
4. Check if session cookies are being sent with requests

The frontend needs to:
- Include authentication cookies in requests
- Have a valid session established
- Have workspace context available
""")

if __name__ == "__main__":
    main()
