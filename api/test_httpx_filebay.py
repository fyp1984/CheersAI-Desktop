#!/usr/bin/env python3
"""Test FileBay connection using httpx library."""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()


def test_with_httpx():
    """Test FileBay connection with httpx."""
    url = os.getenv("GITEA_URL", "https://uat-filebay.cheersai.cloud")
    token = os.getenv("GITEA_TOKEN", "")
    owner = os.getenv("GITEA_OWNER", "")
    repo = os.getenv("GITEA_REPO", "workspace")
    
    if not token or not owner:
        print("Error: GITEA_TOKEN and GITEA_OWNER must be set")
        return
    
    print(f"Testing with httpx...")
    print(f"URL: {url}")
    print(f"Owner: {owner}, Repo: {repo}")
    print("-" * 60)
    
    # Create client with SSL verification disabled
    client = httpx.Client(verify=False, timeout=10.0)
    
    try:
        response = client.get(
            f"{url}/api/v1/repos/{owner}/{repo}/contents/",
            headers={"Authorization": f"token {token}"}
        )
        print(f"✓ Success! Status: {response.status_code}")
        if response.status_code == 200:
            files = response.json()
            print(f"Found {len(files)} items")
            for file in files[:5]:  # Show first 5
                print(f"  - {file.get('name', 'N/A')}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    test_with_httpx()
