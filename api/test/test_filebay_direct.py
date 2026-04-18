#!/usr/bin/env python3
"""Test FileBay connection directly with various SSL configurations."""
import os
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import urllib3
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SSLAdapter(HTTPAdapter):
    """Custom HTTPAdapter with aggressive SSL bypass."""
    
    def init_poolmanager(self, *args, **kwargs):
        """Initialize pool manager with custom SSL context."""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # Allow all TLS versions
        context.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
        context.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
        # Allow all ciphers
        try:
            context.set_ciphers('ALL:@SECLEVEL=0')
        except:
            try:
                context.set_ciphers('DEFAULT:@SECLEVEL=0')
            except:
                pass
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


def test_connection(url, token, owner, repo):
    """Test FileBay connection with different methods."""
    print(f"Testing connection to: {url}")
    print(f"Owner: {owner}, Repo: {repo}")
    print("-" * 60)
    
    # Test 1: Simple verify=False
    print("\n1. Testing with verify=False (simple)...")
    try:
        response = requests.get(
            f"{url}/api/v1/repos/{owner}/{repo}/contents/",
            headers={"Authorization": f"token {token}"},
            timeout=10,
            verify=False
        )
        print(f"   ✓ Success! Status: {response.status_code}")
        if response.status_code == 200:
            files = response.json()
            print(f"   Found {len(files)} items")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Test 2: With custom SSL adapter
    print("\n2. Testing with custom SSL adapter...")
    try:
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        response = session.get(
            f"{url}/api/v1/repos/{owner}/{repo}/contents/",
            headers={"Authorization": f"token {token}"},
            timeout=10,
            verify=False
        )
        print(f"   ✓ Success! Status: {response.status_code}")
        if response.status_code == 200:
            files = response.json()
            print(f"   Found {len(files)} items")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Test 3: Test user endpoint (simpler)
    print("\n3. Testing user endpoint...")
    try:
        response = requests.get(
            f"{url}/api/v1/users/{owner}",
            headers={"Authorization": f"token {token}"},
            timeout=10,
            verify=False
        )
        print(f"   ✓ Success! Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"   User: {user.get('username', 'N/A')}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")


if __name__ == "__main__":
    # Load from environment
    url = os.getenv("GITEA_URL", "https://uat-filebay.cheersai.cloud")
    token = os.getenv("GITEA_TOKEN", "")
    owner = os.getenv("GITEA_OWNER", "")
    repo = os.getenv("GITEA_REPO", "workspace")
    
    if not token or not owner:
        print("Error: GITEA_TOKEN and GITEA_OWNER must be set in .env")
        exit(1)
    
    test_connection(url, token, owner, repo)
