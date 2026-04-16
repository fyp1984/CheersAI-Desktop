#!/usr/bin/env python3
"""Test FileBay connection using pyOpenSSL to force OpenSSL backend."""
import os
from dotenv import load_dotenv

load_dotenv()

# Force urllib3 to use pyOpenSSL
try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
    print("✓ Injected pyOpenSSL into urllib3")
except ImportError:
    print("✗ pyOpenSSL not available, install with: pip install pyopenssl")
    exit(1)

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_with_pyopenssl():
    """Test FileBay connection with pyOpenSSL backend."""
    url = os.getenv("GITEA_URL", "https://uat-filebay.cheersai.cloud")
    token = os.getenv("GITEA_TOKEN", "")
    owner = os.getenv("GITEA_OWNER", "")
    repo = os.getenv("GITEA_REPO", "workspace")
    
    if not token or not owner:
        print("Error: GITEA_TOKEN and GITEA_OWNER must be set")
        return
    
    print(f"\nTesting with pyOpenSSL backend...")
    print(f"URL: {url}")
    print(f"Owner: {owner}, Repo: {repo}")
    print("-" * 60)
    
    try:
        response = requests.get(
            f"{url}/api/v1/repos/{owner}/{repo}/contents/",
            headers={"Authorization": f"token {token}"},
            timeout=10,
            verify=False
        )
        print(f"✓ Success! Status: {response.status_code}")
        if response.status_code == 200:
            files = response.json()
            print(f"Found {len(files)} items")
            for file in files[:5]:
                print(f"  - {file.get('name', 'N/A')}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_with_pyopenssl()
