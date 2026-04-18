#!/usr/bin/env python3
"""Test FileBay connection using urllib3 directly with aggressive SSL bypass."""
import os
import ssl
import urllib3
from dotenv import load_dotenv

load_dotenv()

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_urllib3_direct():
    """Test with urllib3 PoolManager directly."""
    url = os.getenv("GITEA_URL", "https://uat-filebay.cheersai.cloud")
    token = os.getenv("GITEA_TOKEN", "")
    owner = os.getenv("GITEA_OWNER", "")
    repo = os.getenv("GITEA_REPO", "workspace")
    
    if not token or not owner:
        print("Error: GITEA_TOKEN and GITEA_OWNER must be set")
        return
    
    print(f"Testing with urllib3 PoolManager...")
    print(f"URL: {url}")
    print(f"Owner: {owner}, Repo: {repo}")
    print("-" * 60)
    
    # Create custom SSL context
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Try to allow all TLS versions
    try:
        ctx.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
        ctx.maximum_version = ssl.TLSVersion.MAXIMUM_SUPPORTED
    except:
        pass
    
    # Try to set permissive ciphers
    try:
        ctx.set_ciphers('ALL:@SECLEVEL=0')
    except:
        try:
            ctx.set_ciphers('DEFAULT')
        except:
            pass
    
    # Create PoolManager with custom SSL context
    http = urllib3.PoolManager(
        ssl_context=ctx,
        cert_reqs='CERT_NONE',
        assert_hostname=False,
        timeout=urllib3.Timeout(connect=10.0, read=10.0)
    )
    
    try:
        response = http.request(
            'GET',
            f"{url}/api/v1/repos/{owner}/{repo}/contents/",
            headers={"Authorization": f"token {token}"}
        )
        print(f"✓ Success! Status: {response.status}")
        if response.status == 200:
            import json
            files = json.loads(response.data.decode('utf-8'))
            print(f"Found {len(files)} items")
            for file in files[:5]:
                print(f"  - {file.get('name', 'N/A')}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_urllib3_direct()
